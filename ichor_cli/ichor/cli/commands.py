"""Non-interactive commands, with HPC imports deferred until submission."""

import argparse
from pathlib import Path


def positive_int(value):
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def build_parser():
    parser = argparse.ArgumentParser(prog="ichor")
    commands = parser.add_subparsers(dest="command", required=True)
    aimall = commands.add_parser(
        "submit_aimall", help="Submit a points directory to AIMAll."
    )
    aimall.add_argument("points_directory", nargs="?", type=Path, default=Path.cwd())
    aimall.add_argument("--method", default="B3LYP")
    aimall.add_argument("--ncores", type=positive_int, default=2)
    aimall.add_argument("--naat", type=positive_int, default=1)
    aimall.add_argument("--atoms", "--aimall-atoms", dest="aimall_atoms", nargs="+")
    aimall.add_argument("--force", "--force-calculate-ints", dest="force_calculate_ints",
                        action="store_true", help="Recalculate existing integrations.")
    aimall.add_argument("--hold", help="Scheduler job ID to wait for.")
    aimall.add_argument("--script-name")
    aimall.add_argument("--outputs-dir-path", type=Path)
    aimall.add_argument("--errors-dir-path", type=Path)

    choices = {
        "usetwoe": (int, [0, 1, 2]),
        "encomp": (int, [0, 1, 2, 3, 4]),
        "ehren": (int, [0, 1, 2]),
        "shm_lmax": (int, [-1, 0, 1, 2, 3, 4, 5]),
        "boaq": (str, ["auto", "auto_gs2", "auto_gs4"]
                 + ["gs" + str(n) for n in list(range(1, 11)) + list(range(15, 65, 5))]
                 + ["leb" + str(n) for n in [23, 25, 27, 29, 31, 32]]),
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
        aimall.add_argument("--" + name.replace("_", "-"), dest=name,
                            type=value_type, choices=values, default=argparse.SUPPRESS)
    aimall.add_argument("--maxmem", type=positive_int, default=argparse.SUPPRESS)
    aimall.add_argument("--atidsprops", choices=["no", "some", "all"],
                        default=argparse.SUPPRESS, help="'some' corresponds to 0.001.")
    for name in (
        "feynman", "iasprops", "source", "iaswrite", "warn", "delmog",
        "skipint", "f2wonly", "atlaprhocps", "wsp", "saw", "autonnacps",
    ):
        group = aimall.add_mutually_exclusive_group()
        group.add_argument("--" + name, dest=name, action="store_true",
                           default=argparse.SUPPRESS)
        group.add_argument("--no-" + name, dest=name, action="store_false",
                           default=argparse.SUPPRESS)
    return parser


def main(argv=None):
    parser = build_parser()
    options = vars(parser.parse_args(argv))
    options.pop("command")
    path = options["points_directory"].expanduser().resolve()
    if not path.is_dir() or path.suffix != ".pointsdir":
        parser.error("points_directory must be an existing .pointsdir directory")
    options["points_directory"] = path
    for name in ("script_name", "outputs_dir_path", "errors_dir_path"):
        if options[name] is None:
            options.pop(name)
    if options.get("atidsprops") == "some":
        options["atidsprops"] = 0.001

    from ichor.hpc.batch_system import JobID
    from ichor.hpc.main.aimall import submit_points_directory_to_aimall

    if options["hold"] is not None:
        options["hold"] = JobID("", options["hold"])
    job = submit_points_directory_to_aimall(**options)
    if job is None:
        print("There are no AIMAll jobs to submit.")
    else:
        print("Submitted AIMAll job " + str(job.id))
    return 0
