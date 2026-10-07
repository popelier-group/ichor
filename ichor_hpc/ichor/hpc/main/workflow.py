"""Run selected stages on compute nodes, coordinating from the login node."""

import json
import inspect
import time
from dataclasses import dataclass, field
from pathlib import Path

STAGES = ("optimisation", "metadynamics", "diversity", "datagen")


@dataclass
class Workflow:
    output_path: Path
    jobs: dict = field(default_factory=dict)
    data_generation: object = None


def select_stages(stages):
    if not isinstance(stages, (list, tuple)) or not stages:
        raise ValueError("workflow.stages must be a non-empty list of stage names.")
    if any(stage not in STAGES for stage in stages):
        raise ValueError(f"Stages must be one of {', '.join(STAGES)}")
    if len(set(stages)) != len(stages):
        raise ValueError("Each workflow stage may be selected only once.")
    return tuple(stage for stage in STAGES if stage in stages)


def submit_workflow_from_yaml(config_path, stages=None):
    import yaml

    config_path = Path(config_path).resolve()
    with config_path.open() as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ValueError("Workflow YAML must contain a mapping.")
    return submit_workflow(config, config_path.parent, stages)


def submit_workflow(config, base_directory=Path.cwd(), stages=None):
    """Submit only the selected stages in their normal workflow order.

    Keep this process running on the login node while intermediate jobs finish.
    The final requested stage is submitted without waiting. Ctrl-C stops further
    submissions; already submitted jobs remain on the scheduler. Resume by passing
    the remaining stages and setting input.path to the preceding stage's output.
    No jobs are submitted from compute nodes.
    """
    import ichor.hpc.global_variables as settings
    from ichor.core.files import XTB
    from ichor.core.files.mtd import MtdTrajScript
    from ichor.core.files.polus import DiversityScript
    from ichor.hpc.batch_system import NodeType
    from ichor.hpc.main.data_generation import submit_data_generation_from_yaml
    from ichor.hpc.submission_commands import AnacondaCommand, PythonCommand
    from ichor.hpc.submission_script import SubmissionScript

    config = dict(config)
    control = config.pop("workflow", {})
    if not isinstance(control, dict) or control.keys() - {"stages", "directory", "poll_interval"}:
        raise ValueError("Invalid workflow settings.")
    stages = select_stages(stages if stages is not None else control.get("stages", STAGES))
    if settings.BATCH_SYSTEM.current_node() is NodeType.ComputeNode:
        raise ValueError("Start the workflow on a login node.")
    base = Path(base_directory).resolve()

    def path(value):
        value = Path(value).expanduser()
        return value.resolve() if value.is_absolute() else (base / value).resolve()

    inputs = config.get("input", {})
    if not isinstance(inputs, dict) or not inputs.get("path"):
        raise ValueError("input.path is required.")
    current = path(inputs["path"])
    if not current.exists():
        raise ValueError(f"Input does not exist: {current}")
    directory = path(control.get("directory", "workflow_runs"))
    interval = control.get("poll_interval", 30)
    if not isinstance(interval, (int, float)) or interval <= 0:
        raise ValueError("workflow.poll_interval must be positive.")
    sections = {}
    for name in STAGES[:-1]:
        section = config.pop(name, {})
        if not isinstance(section, dict) or section.keys() - {"ncores", "output", "seed_geom", "options"}:
            raise ValueError(f"Invalid {name} settings.")
        if not isinstance(section.get("options", {}), dict):
            raise ValueError(f"{name}.options must contain a mapping.")
        ncores = section.get("ncores", 2)
        if isinstance(ncores, bool) or not isinstance(ncores, int) or ncores < 1:
            raise ValueError(f"{name}.ncores must be a positive integer.")
        sections[name] = section
    unknown = config.keys() - {"input", "electronic_structure", "aim", "database", "csvs"}
    if unknown:
        raise ValueError(f"Unknown workflow sections: {sorted(unknown)}")
    if "metadynamics" in stages:
        cvs = sections["metadynamics"].get("options", {}).get("collective_variables")
        if not cvs or any(not isinstance(cv, list) or len(cv) not in (2, 3, 4)
                          or any(type(i) is not int or i < 1 for i in cv) for cv in cvs):
            raise ValueError("metadynamics.options.collective_variables requires atom index lists of length 2, 3 or 4.")
    if "diversity" in stages and not sections["diversity"].get("output"):
        raise ValueError("diversity.output must name the XYZ file produced by POLUS.")
    if stages[0] == "diversity" and not sections["diversity"].get("seed_geom"):
        raise ValueError("diversity.seed_geom is required when starting at diversity.")
    writers = {"optimisation": XTB, "metadynamics": MtdTrajScript, "diversity": DiversityScript}
    reserved = {"path", "input_xyz_path", "output_xyz_path", "traj_path", "log_path",
                "input_xtb_path", "seed_geom", "output_dir", "filename"}
    for stage in stages:
        if stage == "datagen":
            continue
        allowed = set(inspect.signature(writers[stage]).parameters) - reserved
        invalid = sections[stage].get("options", {}).keys() - allowed
        if invalid:
            raise ValueError(f"Unknown options in {stage}: {sorted(invalid)}")
    result = Workflow(current)
    seed = current
    for stage in stages:
        if stage == "datagen":
            directory.mkdir(parents=True, exist_ok=True)
            config["input"] = {**inputs, "path": str(current)}
            snapshot = directory / "datagen.yaml"
            import yaml
            snapshot.write_text(yaml.safe_dump(config))
            result.data_generation = submit_data_generation_from_yaml(snapshot)
            result.output_path = result.data_generation.points_directory
            break
        section = sections[stage]
        work = directory / stage
        work.mkdir(parents=True, exist_ok=True)
        output = path(section["output"]) if section.get("output") else work / ("optimised.xyz" if stage == "optimisation" else "trajectory_mtd_out.xyz")
        if output.exists():
            raise ValueError(f"Output already exists; resume at the next stage or choose another output: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        script = work / "calculation.py"
        options = dict(section.get("options", {}))
        if stage == "optimisation":
            writer = XTB(script, current, output, work / "opt.traj", work / "opt.log", current, **options)
            writer.set_write_defaults_if_needed()
        elif stage == "metadynamics":
            calculator = options.pop("calculator", "GFN2-xTB")
            options.pop("system_name", None)
            # The existing writer chooses <system_name>_mtd_out.xyz beside its input.
            staged_input = work / "input.xyz"
            writer = MtdTrajScript(script, staged_input, system_name="trajectory", calculator=calculator, **options)
        else:
            seed_path = path(section["seed_geom"]) if section.get("seed_geom") else seed
            if not seed_path.is_file():
                raise ValueError(f"Diversity seed geometry does not exist: {seed_path}")
            writer = DiversityScript(script, seed_path, output.parent, current, **options)
        writer.write()
        marker = work / "completed.json"
        if marker.exists():
            marker.unlink()
        runner = work / "run.py"
        preamble = ""
        if stage == "metadynamics":
            preamble = f"import shutil\nshutil.copyfile({str(current)!r}, {str(staged_input)!r})\n"
        tail = ""
        if stage == "metadynamics" and output != work / "trajectory_mtd_out.xyz":
            tail = f"shutil.move({str(work / 'trajectory_mtd_out.xyz')!r}, {str(output)!r})\n"
        runner.write_text("import runpy\nfrom pathlib import Path\n" + preamble +
                          f"runpy.run_path({str(script)!r}, run_name='__main__')\n" + tail +
                          f"assert Path({str(output)!r}).is_file(), 'Expected stage output was not produced'\n" +
                          f"Path({str(marker)!r}).write_text({json.dumps({'output': str(output)})!r})\n")
        with SubmissionScript(work / "submit.sh", ncores=section.get("ncores", 2), cwd=work) as submission:
            command = AnacondaCommand if stage == "metadynamics" else PythonCommand
            submission.add_command(command(runner))
        job = submission.submit()
        if job is None:
            raise RuntimeError(f"{stage} was not submitted.")
        result.jobs[stage] = job
        print(f"Submitted {stage} job {job.id}; output: {output}", flush=True)
        current = output
        result.output_path = output
        if stage != stages[-1]:
            while any(str(queued.id) == str(job.id) for queued in settings.BATCH_SYSTEM.get_queued_jobs()):
                time.sleep(interval)
            if not marker.is_file() or not output.is_file():
                raise RuntimeError(f"{stage} job {job.id} failed; expected output: {output}")
        if stage == "optimisation":
            seed = output
    return result
