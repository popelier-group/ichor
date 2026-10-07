"""Exercise orchestration without a scheduler or scientific software."""

import importlib.util
import json
import runpy
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from ichor.cli.commands import build_parser

spec = importlib.util.spec_from_file_location(
    "workflow_under_test",
    Path(__file__).resolve().parents[2] / "ichor_hpc/ichor/hpc/main/workflow.py",
)
workflow = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = workflow
spec.loader.exec_module(workflow)


class WorkflowTests(unittest.TestCase):
    def test_selection_and_cli(self):
        self.assertEqual(workflow.select_stages(["datagen", "optimisation"]), ("optimisation", "datagen"))
        self.assertEqual(workflow.select_stages(["diversity"]), ("diversity",))
        for invalid in ([], "datagen", ["unknown"], ["datagen", "datagen"]):
            with self.assertRaises(ValueError):
                workflow.select_stages(invalid)
        parsed = build_parser().parse_args(["workflow", "--stages", "diversity", "datagen"])
        self.assertEqual(parsed.stages, ["diversity", "datagen"])
        self.assertIsNone(build_parser().parse_args(["workflow"]).stages)

    def test_stage_handoffs_and_failure(self):
        modules = {}

        def module(name, **attrs):
            value = ModuleType(name)
            value.__dict__.update(attrs)
            modules[name] = value
            return value

        submitted = []
        complete = [True]

        class Writer:
            def __init__(self, script, *args):
                self.script = script
                self.output = Path(args[1])

            def set_write_defaults_if_needed(self):
                pass

            def write(self):
                self.script.write_text(f"from pathlib import Path\nPath({str(self.output)!r}).write_text('geometry')\n")

        class Mtd(Writer):
            def __init__(self, script, input_path, system_name=None, calculator=None, collective_variables=None):
                self.script = script
                self.output = input_path.parent / (system_name + "_mtd_out.xyz")

        class Diversity(Writer):
            def __init__(self, script, seed, output_dir, trajectory):
                self.script = script
                self.output = output_dir / "sample.xyz"

        class Submission:
            def __init__(self, script, **kwargs):
                self.script = script

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def add_command(self, command):
                self.runner = command

            def submit(self):
                submitted.append(self.script.parent.name)
                if complete[0]:
                    runpy.run_path(str(self.runner))
                return SimpleNamespace(id=str(len(submitted)))

        node = SimpleNamespace(ComputeNode=object())
        settings = module("ichor.hpc.global_variables", BATCH_SYSTEM=SimpleNamespace(
            current_node=lambda: None, get_queued_jobs=lambda: []))
        module("ichor", hpc=module("ichor.hpc", global_variables=settings))
        module("ichor.core.files", XTB=Writer)
        module("ichor.core.files.mtd", MtdTrajScript=Mtd)
        module("ichor.core.files.polus", DiversityScript=Diversity)
        module("ichor.hpc.batch_system", NodeType=node)
        datagen = Mock(return_value=SimpleNamespace(points_directory=Path("sample.pointsdir")))
        module("ichor.hpc.main.data_generation", submit_data_generation_from_yaml=datagen)
        module("ichor.hpc.submission_commands", PythonCommand=lambda p: p, AnacondaCommand=lambda p: p)
        module("ichor.hpc.submission_script", SubmissionScript=Submission)
        module("yaml", safe_dump=json.dumps, safe_load=json.loads)

        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, modules):
            base = Path(tmp)
            (base / "input.xyz").write_text("geometry")
            config = {"input": {"path": "input.xyz"},
                      "metadynamics": {"options": {"collective_variables": [[1, 2]]}},
                      "diversity": {"output": "workflow_runs/diversity/sample.xyz"}}
            result = workflow.submit_workflow(config, base)
            self.assertEqual(submitted, ["optimisation", "metadynamics", "diversity"])
            self.assertEqual(result.output_path, Path("sample.pointsdir"))
            import yaml
            snapshot = yaml.safe_load(datagen.call_args.args[0].read_text())
            self.assertEqual(Path(snapshot["input"]["path"]), base / "workflow_runs/diversity/sample.xyz")
            # CLI/API selection overrides YAML and does not insert skipped stages.
            config["workflow"] = {"directory": "selected_run", "stages": ["metadynamics"]}
            submitted.clear()
            workflow.submit_workflow(config, base, stages=["datagen", "optimisation"])
            self.assertEqual(submitted, ["optimisation"])
            snapshot = yaml.safe_load(datagen.call_args.args[0].read_text())
            self.assertEqual(Path(snapshot["input"]["path"]), base / "selected_run/optimisation/optimised.xyz")
            config["workflow"] = {"directory": "yaml_run", "stages": ["metadynamics"]}
            submitted.clear()
            workflow.submit_workflow(config, base)
            self.assertEqual(submitted, ["metadynamics"])
            complete[0] = False
            config["workflow"] = {"directory": "failed_run"}
            submitted.clear()
            with self.assertRaisesRegex(RuntimeError, "optimisation.*failed"):
                workflow.submit_workflow(config, base)
            self.assertEqual(submitted, ["optimisation"])


if __name__ == "__main__":
    unittest.main()
