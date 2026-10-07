"""Non-interactive commands, with HPC imports deferred until submission."""

import argparse
import math
from pathlib import Path


def positive_int(value):
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def positive_float(value):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise argparse.ArgumentTypeError("must be a finite positive number")
    return value


def build_parser():
    parser = argparse.ArgumentParser(prog="ichor")
    commands = parser.add_subparsers(dest="command", required=True)
    opt = commands.add_parser("opt", help="Submit a single-geometry optimisation.")
    backends = opt.add_subparsers(dest="backend", required=True)
    for backend in ("gaussian", "xtb"):
        optimisation = backends.add_parser(
            backend, help=f"Optimise an XYZ geometry with {backend}.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        optimisation.add_argument("input_xyz_path", type=Path, help="Starting XYZ file (first geometry is used).")
        optimisation.add_argument("--ncores", "--cores", type=positive_int, default=2, help="CPU cores.")
        optimisation.add_argument("--hold", help="Scheduler job ID to wait for.")
        optimisation.add_argument("--overwrite", "--overwrite-existing", dest="overwrite_existing",
                                  action="store_true", help="Replace the existing optimisation directory.")
        if backend == "gaussian":
            optimisation.add_argument("--method", default="b3lyp", help="Electronic structure method.")
            optimisation.add_argument("--basis-set", default="6-31+g(d,p)", help="Basis set.")
            optimisation.add_argument("--keywords", nargs="+", default=["opt"],
                                      help="Route keywords; opt is added if absent.")
            optimisation.add_argument("--charge", type=int, default=argparse.SUPPRESS)
            optimisation.add_argument("--spin-multiplicity", type=positive_int, default=argparse.SUPPRESS)
            optimisation.add_argument("--title", default=argparse.SUPPRESS)
            optimisation.add_argument("--link0", nargs="+", default=argparse.SUPPRESS,
                                      help="Link 0 settings without the leading percent sign.")
            optimisation.add_argument("--output-chk", action="store_true", default=argparse.SUPPRESS)
        else:
            optimisation.add_argument("--method", default="GFN2-xTB", help="ASE xTB calculator method.")
            optimisation.add_argument("--solvent", default="none", help="Solvent name.")
            optimisation.add_argument("--electronic-temperature", type=positive_int, default=300,
                                      help="Electronic temperature in K.")
            optimisation.add_argument("--max-iterations", type=positive_int, default=2048,
                                      help="Maximum calculator iterations.")
            optimisation.add_argument("--fmax", type=positive_float, default=0.01,
                                      help="Force convergence in eV/Angstrom.")
    datagen = commands.add_parser(
        "datagen", aliases=["submit_datagen"], help="Submit the data-generation workflow from YAML."
    )
    datagen.add_argument(
        "config", nargs="?", type=Path, default=Path("ichor_workflow.yaml"),
        help="Workflow YAML file (default: ichor_workflow.yaml in the current directory).",
    )
    gaussian = commands.add_parser(
        "submit_gaussian", help="Write Gaussian inputs and submit a points directory."
    )
    gaussian.add_argument("points_directory", nargs="?", type=Path, default=Path.cwd())
    gaussian.add_argument("--ncores", type=positive_int, default=2)
    gaussian.add_argument("--method", default=argparse.SUPPRESS)
    gaussian.add_argument("--basis-set", default=argparse.SUPPRESS)
    gaussian.add_argument("--keywords", nargs="+", default=argparse.SUPPRESS)
    gaussian.add_argument("--charge", type=int, default=argparse.SUPPRESS)
    gaussian.add_argument("--spin-multiplicity", type=positive_int, default=argparse.SUPPRESS)
    gaussian.add_argument("--title", default=argparse.SUPPRESS)
    gaussian.add_argument("--link0", nargs="+", default=argparse.SUPPRESS,
                          help="Link 0 settings without the leading percent sign.")
    gaussian.add_argument("--output-chk", action="store_true", default=argparse.SUPPRESS)
    gaussian.add_argument("--overwrite-existing", action="store_true",
                          help="Replace existing GJF files with the requested settings.")
    gaussian.add_argument("--force", "--force-calculate-wfn", dest="force_calculate_wfn",
                          action="store_true", help="Recalculate existing wavefunctions.")
    gaussian.add_argument("--hold", help="Scheduler job ID to wait for.")
    gaussian.add_argument("--script-name")
    gaussian.add_argument("--outputs-dir-path", type=Path)
    gaussian.add_argument("--errors-dir-path", type=Path)
    aimall = commands.add_parser(
        "submit_aimall", help="Submit a points directory to AIMAll."
    )
    aimall.add_argument("points_directory", nargs="?", type=Path, default=Path.cwd())
    aimall.add_argument("--method", default="B3LYP")
    aimall.add_argument("--ncores", type=positive_int, default=2)
    aimall.add_argument("--naat", type=positive_int, default=1)
    aimall.add_argument("--atoms", "--aimall-atoms", dest="aimall_atoms", nargs="+")
    aimall.add_argument(
        "--force",
        "--force-calculate-ints",
        dest="force_calculate_ints",
        action="store_true",
        help="Recalculate existing integrations.",
    )
    aimall.add_argument("--hold", help="Scheduler job ID to wait for.")
    aimall.add_argument("--script-name")
    aimall.add_argument("--outputs-dir-path", type=Path)
    aimall.add_argument("--errors-dir-path", type=Path)

    choices = {
        "usetwoe": (int, [0, 1, 2]),
        "encomp": (int, [0, 1, 2, 3, 4]),
        "ehren": (int, [0, 1, 2]),
        "shm_lmax": (int, [-1, 0, 1, 2, 3, 4, 5]),
        "boaq": (
            str,
            ["auto", "auto_gs2", "auto_gs4"]
            + ["gs" + str(n) for n in list(range(1, 11)) + list(range(15, 65, 5))]
            + ["leb" + str(n) for n in [23, 25, 27, 29, 31, 32]],
        ),
        "iasmesh": (str, ["fine", "medium", "veryfine", "superfine"]),
        "bim": (str, ["auto", "proaim", "promega", "promega1", "promega5"]),
        "capture": (str, ["auto", "basic", "extended"]),
        "magprops": (str, ["none", "gaim", "csgtb", "giao"]),
        "scp": (str, ["false", "some", "true"]),
        "f2w": (str, ["wfx", "wfn"]),
        "mir": (str, ["auto", "custom"]),
        "cpconn": (str, ["moderate", "complex", "simple", "basic"]),
        "intveeaa": (str, ["old", "new"]),
        "verifyw": (str, ["no", "yes", "only"]),
    }
    for name, (value_type, values) in choices.items():
        aimall.add_argument(
            "--" + name.replace("_", "-"),
            dest=name,
            type=value_type,
            choices=values,
            default=argparse.SUPPRESS,
        )
    aimall.add_argument("--maxmem", type=positive_int, default=argparse.SUPPRESS)
    aimall.add_argument(
        "--atidsprops",
        choices=["no", "some", "all"],
        default=argparse.SUPPRESS,
        help="'some' corresponds to 0.001.",
    )
    for name in (
        "feynman",
        "iasprops",
        "source",
        "iaswrite",
        "warn",
        "delmog",
        "skipint",
        "f2wonly",
        "atlaprhocps",
        "wsp",
        "saw",
        "autonnacps",
    ):
        group = aimall.add_mutually_exclusive_group()
        group.add_argument(
            "--" + name, dest=name, action="store_true", default=argparse.SUPPRESS
        )
        group.add_argument(
            "--no-" + name, dest=name, action="store_false", default=argparse.SUPPRESS
        )
    for name, legacy in (("gaussian", gaussian), ("aimall", aimall)):
        program = commands.add_parser(name, help=f"Run or inspect {name} calculations.")
        actions = program.add_subparsers(dest="action", required=True)
        actions.add_parser("run", parents=[legacy], add_help=False)
        status = actions.add_parser("status", help="Show calculation progress.")
        status.add_argument("points_directory", nargs="?", type=Path, default=Path.cwd())
    return parser


def main(argv=None):
    parser = build_parser()
    options = vars(parser.parse_args(argv))
    command = options.pop("command")
    action = options.pop("action", "run")
    if command == "opt":
        backend = options.pop("backend")
        path = options["input_xyz_path"].expanduser().resolve()
        if not path.is_file() or path.suffix.lower() != ".xyz":
            parser.error("input_xyz_path must be an existing .xyz file")
        options["input_xyz_path"] = path
        if options["hold"] is not None:
            from ichor.hpc.batch_system import JobID

            options["hold"] = JobID("", options["hold"])
        if backend == "gaussian":
            from ichor.hpc.main.gaussian import submit_single_gaussian_xyz

            keywords = options["keywords"]
            if not any(k.lower().split("=", 1)[0].split("(", 1)[0] == "opt" for k in keywords):
                keywords.insert(0, "opt")
            job = submit_single_gaussian_xyz(**options)
            program = "gaussian"
        else:
            from ichor.hpc.main.ase import submit_single_ase_xyz
            from ichor.hpc.useful_functions import XTBNotFound

            options["overwrite"] = options.pop("overwrite_existing")
            try:
                job = submit_single_ase_xyz(**options)
            except XTBNotFound as error:
                parser.exit(1, f"xTB optimisation not submitted: {error}\n")
            program = "ase"
        from ichor.hpc.main.opt import single_geometry_optimisation_directory

        directory = single_geometry_optimisation_directory(path.stem, program)
        if job is None:
            print(f"Optimisation not submitted: {directory} already exists; use --overwrite to replace it.")
            return 1
        print(f"Submitted {backend} optimisation job {job.id}")
        print(f"Optimisation directory: {directory}")
        print(f"Optimised geometry: {directory / (path.stem + '_optimised.xyz')}")
        return 0
    if command in ("datagen", "submit_datagen"):
        config = options["config"].expanduser().resolve()
        if not config.is_file():
            parser.error(f"workflow YAML file does not exist: {config}")

        from ichor.hpc.main.data_generation import submit_data_generation_from_yaml

        result = submit_data_generation_from_yaml(config)
        print(f"Points directory: {result.points_directory}")
        for name in ("gaussian", "aimall", "database", "csvs"):
            job = getattr(result, name)
            if job is not None:
                print(f"Submitted {name} job {job.id}")
        return 0

    path = options["points_directory"].expanduser().resolve()
    if not path.is_dir() or path.suffix != ".pointsdir":
        parser.error("points_directory must be an existing .pointsdir directory")
    options["points_directory"] = path
    if action == "status":
        from ichor.hpc.calculation_status import print_status

        print_status(path, command)
        return 0
    for name in ("script_name", "outputs_dir_path", "errors_dir_path"):
        if options[name] is None:
            options.pop(name)
    if options.get("atidsprops") == "some":
        options["atidsprops"] = 0.001

    from ichor.hpc.batch_system import JobID
    if options["hold"] is not None:
        options["hold"] = JobID("", options["hold"])
    if command in ("gaussian", "submit_gaussian"):
        from ichor.hpc.main.gaussian import submit_points_directory_to_gaussian

        software = "Gaussian"
        try:
            job = submit_points_directory_to_gaussian(**options)
        except ValueError as error:
            if str(error) != "There are no jobs to submit in the submission script.":
                raise
            job = None
    else:
        from ichor.hpc.main.aimall import submit_points_directory_to_aimall

        software = "AIMAll"
        job = submit_points_directory_to_aimall(**options)
    if job is None:
        print("There are no " + software + " jobs to submit.")
    else:
        print("Submitted " + software + " job " + str(job.id))
    return 0
