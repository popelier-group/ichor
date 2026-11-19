"""The job submission options menu, which changes the ``hpc`` block of the ichor config
for the machine ichor is running on: which partitions jobs go to, how long they may run
for, and how much memory a core brings.

It can be opened from every menu by pressing ``j``, as these are settings that tend to
be wanted just before submitting something, from whichever menu that is. Each change is
written to the config file straight away and applies to every job submitted after it,
in this session and later ones, so nothing has to be saved or restarted.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Mapping, MutableMapping, Optional, Union

import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions, shorten_path_for_display
from ichor.cli.useful_functions import (
    print_summary_and_pause,
    user_input_bool,
    user_input_free_flow,
    user_input_int,
)
from ichor.hpc import hpc_settings
from ichor.hpc.batch_system import SLURM
from ichor.hpc.detect_hpc import (
    detect_partitions,
    DetectionUnavailable,
    Partition,
    sinfo_is_available,
    walltime_for_config,
)
from ichor.hpc.global_variables import get_param_from_config

try:
    from termcolor import colored
except ImportError:

    def colored(text, *args, **kwargs):
        return text


JOB_SUBMISSION_MENU_DESCRIPTION = MenuDescription(
    "Job Submission Options",
    subtitle="Changes are saved to your config file and kept for all future jobs.",
)

# the key that opens this menu from any other
JOB_SUBMISSION_MENU_KEY = "j"

# the menu items, which messages elsewhere in the menu refer the user to
SEND_JOBS_BY_SIZE = "Send jobs of a given size to a partition, e.g. 2-32 cores"
SWAP_PARTITION = "Send a partition's jobs somewhere else, e.g. to multicore_small"
STOP_USING_PARTITION = "Stop using a partition"
CHANGE_TIME_LIMIT = "Change the time limit"
CHANGE_MEMORY = "Change the memory per core"

# jobs which always ask for 1 core, as they are too quick to be worth more, and so are
# what a partition taking 1 core jobs is kept for
ONE_CORE_JOBS_NOTE = (
    "That includes centring a trajectory on an atom (Analysis menu) and writing out "
    "the .xyz after a Gaussian optimisation, which always use 1 core."
)


def covers_one_core(core_range) -> bool:
    """Whether a range of core counts includes 1 core jobs."""

    return core_range[0] <= 1 <= core_range[1]


def partition_problems() -> List[str]:
    """Overlapping ranges and core counts no partition covers, worded for the user."""

    ranges = hpc_settings.partitions(current_hpc_block())
    problems = hpc_settings.range_problems(ranges)
    # the 1 core jobs cannot be moved by giving them more cores, so say which they are
    if any(covers_one_core(gap) for gap in hpc_settings.uncovered_core_counts(ranges)):
        problems.append(ONE_CORE_JOBS_NOTE)

    return problems


def current_hpc_block() -> dict:
    """The ``hpc`` block of the machine ichor is running on, as last read."""

    return (
        get_param_from_config(
            ichor.hpc.global_variables.ICHOR_CONFIG,
            ichor.hpc.global_variables.MACHINE,
            "hpc",
            default={},
        )
        or {}
    )


def format_cores(low: int, high: int) -> str:
    """e.g. ``1 core`` or ``2-168 cores``"""

    return (
        "1 core"
        if low == high == 1
        else (f"{low} cores" if low == high else f"{low}-{high} cores")
    )


def format_memory(memory) -> str:
    """Memory per core, whether one number or one per partition."""

    if memory is None:
        return (
            f"not set ({ichor.hpc.global_variables.DEFAULT_MEMORY_PER_CORE_GB} GB "
            "is assumed)"
        )
    if isinstance(memory, Mapping):
        return ", ".join(f"{name} {gb:g} GB" for name, gb in memory.items())

    return f"{memory:g} GB"


def format_walltime(walltime) -> str:
    """The time limit as the menu shows it."""

    if walltime is None:
        return f"{ichor.hpc.global_variables.DEFAULT_MAX_WALLTIME} (the default)"
    if str(walltime).strip().lower() == hpc_settings.NO_WALLTIME:
        return "none (the partition's own limit applies)"

    return str(walltime)


def partition_table(numbered: bool = False) -> List[str]:
    """The configured partitions, smallest jobs first, one per line, e.g.
    ``1 core         serial      5 GB per core``. Memory is only shown when it is
    given per partition, as otherwise it is the same for all of them."""

    hpc = current_hpc_block()
    ranges = hpc_settings.partitions(hpc)
    memory = hpc.get("memory_per_core_gb")

    rows = sorted(ranges.items(), key=lambda item: item[1])
    cores_width = max((len(format_cores(*r)) for _, r in rows), default=0)
    name_width = max((len(name) for name, _ in rows), default=0)

    lines = []
    for i, (name, core_range) in enumerate(rows, start=1):
        line = f"{format_cores(*core_range):<{cores_width}}   {name:<{name_width}}"
        if isinstance(memory, Mapping):
            gb = memory.get(name)
            line += f"   {gb:g} GB per core" if gb is not None else "   memory not set"
        lines.append((f"{i}. " if numbered else "") + line.rstrip())

    return lines


@dataclass
class JobSubmissionMenuOptions(MenuOptions):
    """Shows the current job submission options. They are read from the config each
    time the menu is drawn rather than stored here, as they are the config's to keep,
    and could have been changed by hand since."""

    def __str__(self):
        hpc = current_hpc_block()
        config_path = ichor.hpc.global_variables.ICHOR_CONFIG_PATH

        def value(text) -> str:
            return colored(str(text), "green")

        lines = [
            "-- Machine: "
            + value(ichor.hpc.global_variables.MACHINE or "not in the config"),
            "-- Config file: "
            + value(shorten_path_for_display(config_path) if config_path else "none"),
            "-- Jobs are sent to:",
        ]
        table = partition_table()
        lines += [f"     {value(line)}" for line in table] or [
            f"     {value('no partitions configured')}"
        ]
        lines.append(
            "-- Time limit: " + value(format_walltime(hpc.get("max_walltime")))
        )
        memory = hpc.get("memory_per_core_gb")
        if not isinstance(memory, Mapping):
            lines.append("-- Memory per core: " + value(format_memory(memory)))

        return "\n".join(lines) + "\n"

    def check_can_edit(self) -> Optional[str]:
        """Whether there is a config and a block in it for this machine to change."""

        return cannot_edit_reason()

    def check_partitions(self) -> Optional[str]:
        """Overlapping ranges, and core counts no partition covers."""

        return "\n! ".join(partition_problems()) or None

    def check_memory_per_partition(self) -> Optional[str]:
        """Partitions with no memory given for them, when memory is per partition.
        Gaussian jobs sent to one cannot be sized and are refused."""

        hpc = current_hpc_block()
        memory = hpc.get("memory_per_core_gb")
        if not isinstance(memory, Mapping):
            return None

        missing = [name for name in hpc_settings.partitions(hpc) if name not in memory]
        if missing:
            return (
                f"No memory per core is set for {', '.join(missing)}. Use "
                f"'{CHANGE_MEMORY}' to set it."
            )

    def check_time_limit(self) -> Optional[str]:
        """A time limit SLURM would reject."""

        walltime = current_hpc_block().get("max_walltime")
        if walltime is None:
            return None
        try:
            hpc_settings.normalise_walltime(walltime)
        except hpc_settings.HpcSettingsError as error:
            return str(error)


job_submission_menu_options = JobSubmissionMenuOptions()


def cannot_edit_reason() -> Optional[str]:
    """Why the options cannot be changed here, or None if they can."""

    if ichor.hpc.global_variables.ICHOR_CONFIG_PATH is None:
        return (
            "No ichor config file was found. Run `ichor-config-init` to create one "
            "first."
        )
    if not ichor.hpc.global_variables.MACHINE:
        return (
            "This machine has no block in the config file, so there are no settings "
            "to change. Add one first (see `ichor-config-init --detect`)."
        )


def report_cannot_edit() -> bool:
    """Says why the options cannot be changed here, if they cannot.

    :return: True if they cannot, so that the caller stops.
    """

    reason = cannot_edit_reason()
    if reason:
        print_summary_and_pause("NOTHING CHANGED", notes=[reason])

    return reason is not None


# what sinfo reported, read once a session as it can take a moment to answer
_queue_partitions_cache: Optional[List[Partition]] = None


def queue_partitions() -> List[Partition]:
    """The partitions SLURM reports on this cluster, or an empty list when that cannot
    be found out (not SLURM, or sinfo not working)."""

    global _queue_partitions_cache

    if _queue_partitions_cache is None:
        _queue_partitions_cache = []
        if ichor.hpc.global_variables.BATCH_SYSTEM is SLURM and sinfo_is_available():
            try:
                _queue_partitions_cache = detect_partitions()
            except DetectionUnavailable:
                pass

    return _queue_partitions_cache


def print_queue_partitions():
    """Lists the partitions the queue has, so that a name can be picked from them."""

    partitions = queue_partitions()
    if not partitions:
        return

    print("Partitions on this cluster (from sinfo):")
    for p in partitions:
        default = " (default)" if p.is_default else ""
        print(
            f"  {p.name}{default}: {p.cores_per_node} cores per node, time limit "
            f"{walltime_for_config(p.time_limit)}"
        )
    print()


def print_configured_partitions(numbered: bool = False):
    """Shows where jobs are sent now, numbered when one is to be chosen."""

    print("Jobs are currently sent to:")
    for line in partition_table(numbered) or ["no partitions configured"]:
        print(f"  {line}")
    print()


def queue_partition(name: str) -> Optional[Partition]:
    """What sinfo reported for a partition, if it reported one by that name."""

    return next((p for p in queue_partitions() if p.name == name), None)


def confirm_unknown_partition(name: str) -> bool:
    """Checks a partition name against what the queue has, asking before using one it
    does not, as a typo is otherwise only found when sbatch rejects a job."""

    partitions = queue_partitions()
    if not partitions or queue_partition(name) is not None:
        return True

    return bool(
        user_input_bool(
            f"{name} is not one of the partitions sinfo reports. Use it anyway? "
            "(yes/no): ",
            False,
        )
    )


def choose_configured_partition(prompt: str) -> Optional[str]:
    """Asks for one of the configured partitions, by number or by name.

    :param prompt: The question, which is followed by how to answer it.
    :return: The partition's name, or None if nothing was chosen.
    """

    ranges = hpc_settings.partitions(current_hpc_block())
    if not ranges:
        print_summary_and_pause(
            "NO PARTITIONS CONFIGURED",
            notes=[f"Add one with '{SEND_JOBS_BY_SIZE}'."],
        )
        return None

    print_configured_partitions(numbered=True)
    # numbered in the order the table shows them, smallest jobs first
    names = [name for name, _ in sorted(ranges.items(), key=lambda item: item[1])]

    while True:
        answer = user_input_free_flow(f"{prompt} (number or name, enter to cancel): ")
        if not answer:
            return None
        answer = answer.strip()
        if answer in ranges:
            return answer
        if answer.isdigit() and 1 <= int(answer) <= len(names):
            return names[int(answer) - 1]
        print(f"{answer} is not one of the partitions above.")


def ask_partition_name(prompt: str) -> Optional[str]:
    """Asks for the name of a partition, checking it against what the queue has.

    :return: The name, or None if nothing was given or the user backed out.
    """

    name = user_input_free_flow(f"{prompt} (enter to cancel): ")
    if not name or not name.strip():
        return None
    name = name.strip()

    return name if confirm_unknown_partition(name) else None


def user_input_positive_float(prompt: str, default: Optional[float]) -> Optional[float]:
    """Asks for a number above zero, returning ``default`` if nothing is typed."""

    while True:
        answer = user_input_free_flow(prompt)
        if not answer:
            return default
        try:
            value = float(answer)
        except ValueError:
            print(f"{answer} is not a number.")
            continue
        if value <= 0:
            print("It must be more than 0.")
            continue
        return value


def with_default(prompt: str, default) -> str:
    """Adds the answer used when nothing is typed to a prompt, e.g. ``From [2]: ``."""

    return f"{prompt} [{default:g}]: " if default else f"{prompt}: "


def apply_change(
    change: Callable[[MutableMapping], None],
    title: str,
    details: Dict[str, object],
    notes: Optional[List[str]] = None,
):
    """Makes a change to the hpc block in the config file, reloads the config so that
    every job submitted from now on uses it, and says what was done.

    :param change: Changes the ``hpc`` block it is given.
    :param title: The headline of the summary shown once it has been saved.
    :param details: What was changed, shown in the summary.
    :param notes: Anything else to say in the summary.
    """

    if report_cannot_edit():
        return

    config_path = ichor.hpc.global_variables.ICHOR_CONFIG_PATH

    try:
        with hpc_settings.edit_hpc_block(
            config_path, ichor.hpc.global_variables.MACHINE
        ) as hpc:
            change(hpc)
    except hpc_settings.HpcSettingsError as error:
        print_summary_and_pause(
            "NOTHING CHANGED", notes=[str(error), "The config file was not changed."]
        )
        return
    except OSError as error:
        print_summary_and_pause(
            "NOTHING CHANGED",
            notes=[f"The config file could not be written: {error}"],
        )
        return

    ichor.hpc.global_variables.reload_config()
    ichor.hpc.global_variables.LOGGER.info(f"{title}: {details}")

    problems = partition_problems()
    print_summary_and_pause(
        title,
        details,
        (notes or [])
        + problems
        + [
            # the name rather than the path, which the menu shows already and which
            # would be broken across lines here
            f"Saved to {config_path.name}, so it is used for every job submitted from "
            "now on, in this and later ichor sessions, until it is changed again. "
            "Jobs already in the queue keep the settings they were submitted with. "
            "The previous version of the config is kept in "
            f"{hpc_settings.backup_path(config_path).name}."
        ],
    )


class JobSubmissionFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def send_jobs_by_size():
        """Sends jobs of a range of core counts to a partition, e.g. 2-32 cores to
        multicore_small. Partitions that took any of those jobs before have them taken
        off them (after asking), so each job size has one place to go."""

        if report_cannot_edit():
            return

        print_queue_partitions()
        print_configured_partitions()

        name = ask_partition_name("Partition to send them to")
        if name is None:
            return

        hpc = current_hpc_block()
        ranges = hpc_settings.partitions(hpc)
        on_queue = queue_partition(name)

        if name in ranges:
            default_low, default_high = ranges[name]
        else:
            # a gap is the likeliest thing a new partition is for
            gaps = hpc_settings.uncovered_core_counts(ranges)
            default_low = gaps[0][0] if gaps else None
            default_high = on_queue.cores_per_node if on_queue else None

        print(
            f"\nWhich jobs should go to {name}? Give the number of cores they ask for."
        )
        low = user_input_int(
            with_default("  From", default_low), default_low, minimum=1
        )
        if low is None:
            return
        high = user_input_int(
            with_default("  Up to", default_high), default_high, minimum=low
        )
        if high is None:
            return

        if on_queue and on_queue.cores_per_node and high > on_queue.cores_per_node:
            if not user_input_bool(
                f"The nodes of {name} have {on_queue.cores_per_node} cores, so a job "
                f"asking for {high} cannot run there. Use {high} anyway? (yes/no): ",
                False,
            ):
                return

        new_range = (low, high)
        trims, removals = [], []
        for other, other_range in hpc_settings.overlapping_partitions(
            ranges, name, new_range
        ).items():
            pieces = hpc_settings.remaining_range(other_range, new_range)
            if len(pieces) > 1:
                print_summary_and_pause(
                    "NOTHING CHANGED",
                    notes=[
                        f"{other} takes jobs of {format_cores(*other_range)}, and "
                        f"{format_cores(low, high)} is in the middle of that, which "
                        f"would leave {other} with two separate ranges. A partition "
                        "can only have one, so choose a range at one end of "
                        f"{other}'s instead."
                    ],
                )
                return
            if pieces:
                trims.append((other, other_range, pieces[0]))
            else:
                removals.append((other, other_range))

        knock_on = [
            f"{other} goes from {format_cores(*old)} to {format_cores(*new)}"
            for other, old, new in trims
        ] + [
            f"{other} ({format_cores(*old)}) is no longer used, as all its jobs now "
            f"go to {name}"
            for other, old in removals
        ]
        if knock_on:
            print("\nSome of these jobs go to another partition now, so:")
            for line in knock_on:
                print(f"  {line}")
            if not user_input_bool("Go ahead? (yes/no): ", False):
                return

        memory = hpc.get("memory_per_core_gb")
        partition_memory = None
        if isinstance(memory, Mapping) and name not in memory:
            suggested = (
                round(on_queue.memory_per_core_gb, 1)
                if on_queue and on_queue.memory_per_core_gb
                else min(memory.values(), default=None)
            )
            partition_memory = user_input_positive_float(
                with_default(f"Memory per core on {name}, in GB", suggested), suggested
            )
            if partition_memory is None:
                return

        def change(hpc):
            for other, _ in removals:
                hpc_settings.remove_partition(hpc, other)
            for other, _, _ in trims:
                hpc_settings.trim_partition(hpc, other, new_range)
            hpc_settings.set_partition(hpc, name, low, high)
            if partition_memory is not None:
                hpc_settings.set_partition_memory_per_core_gb(
                    hpc, name, partition_memory
                )

        details = {"Jobs of": format_cores(low, high), "Now go to": name}
        if partition_memory is not None:
            details["Memory per core"] = f"{partition_memory:g} GB"
        apply_change(change, "PARTITION CHANGED", details, knock_on)

    @staticmethod
    def swap_partition():
        """Sends all of one partition's jobs to another, e.g. multicore's to
        multicore_small, keeping the job sizes it takes."""

        old = choose_configured_partition("Which partition's jobs should move?")
        if old is None:
            return

        cores = format_cores(*hpc_settings.partitions(current_hpc_block())[old])
        print()
        print_queue_partitions()
        new = ask_partition_name(f"Send its jobs ({cores}) to")
        if new is None:
            return

        apply_change(
            lambda hpc: hpc_settings.rename_partition(hpc, old, new),
            "PARTITION CHANGED",
            {"Jobs of": cores, "Went to": old, "Now go to": new},
        )

    @staticmethod
    def stop_using_partition():
        """Stops sending jobs to a partition."""

        name = choose_configured_partition("Which partition should no longer be used?")
        if name is None:
            return

        core_range = hpc_settings.partitions(current_hpc_block())[name]
        cores = format_cores(*core_range)
        print(
            f"\nJobs of {cores} will have nowhere to go until another partition takes "
            "them."
        )
        if covers_one_core(core_range):
            print(f"{ONE_CORE_JOBS_NOTE} They cannot be submitted without it.")
        if not user_input_bool(f"Stop using {name}? (yes/no): ", False):
            return

        apply_change(
            lambda hpc: hpc_settings.remove_partition(hpc, name),
            "PARTITION NO LONGER USED",
            {"Partition": name, "Jobs it took": cores},
            [f"Use '{SEND_JOBS_BY_SIZE}' to send jobs of {cores} somewhere else."],
        )

    @staticmethod
    def change_time_limit():
        """Changes how long jobs may run for."""

        if report_cannot_edit():
            return

        current = current_hpc_block().get("max_walltime")
        print(f"Jobs may currently run for: {format_walltime(current)}\n")
        print_queue_partitions()
        print(
            "Write it as days-hours (3-0 is three days), hours:minutes:seconds "
            f"(12:00:00), or {hpc_settings.NO_WALLTIME} to use the partition's own "
            "limit.\n"
        )

        while True:
            answer = user_input_free_flow("New time limit (enter to cancel): ")
            if not answer:
                return
            try:
                walltime = hpc_settings.normalise_walltime(answer)
                break
            except hpc_settings.HpcSettingsError as error:
                print(error)

        apply_change(
            lambda hpc: hpc_settings.set_max_walltime(hpc, walltime),
            "TIME LIMIT CHANGED",
            {"Was": format_walltime(current), "Now": format_walltime(walltime)},
        )

    @staticmethod
    def change_memory_per_core():
        """Changes how much memory a core brings, either one number for the whole
        machine or one per partition."""

        if report_cannot_edit():
            return

        hpc = current_hpc_block()
        current = hpc.get("memory_per_core_gb")
        ranges = hpc_settings.partitions(hpc)
        print(f"Memory per core is currently: {format_memory(current)}\n")

        per_partition = False
        if len(ranges) > 1:
            per_partition = user_input_bool(
                "Do the partitions have different amounts of memory per core? "
                f"(yes/no) [{'yes' if isinstance(current, Mapping) else 'no'}]: ",
                isinstance(current, Mapping),
            )

        value: Union[float, Dict[str, float]]
        if per_partition:
            value = {}
            for name in ranges:
                on_queue = queue_partition(name)
                if isinstance(current, Mapping) and name in current:
                    suggested = current[name]
                elif on_queue and on_queue.memory_per_core_gb:
                    suggested = round(on_queue.memory_per_core_gb, 1)
                elif current is not None and not isinstance(current, Mapping):
                    suggested = current
                else:
                    suggested = None
                gb = user_input_positive_float(
                    with_default(f"Memory per core on {name}, in GB", suggested),
                    suggested,
                )
                if gb is None:
                    return
                value[name] = gb
        else:
            suggested = (
                min(current.values(), default=None)
                if isinstance(current, Mapping)
                else current
            )
            value = user_input_positive_float(
                with_default("Memory per core, in GB", suggested), suggested
            )
            if value is None:
                return

        apply_change(
            lambda hpc: hpc_settings.set_memory_per_core_gb(hpc, value),
            "MEMORY PER CORE CHANGED",
            {"Was": format_memory(current), "Now": format_memory(value)},
            [
                "Asking for more memory than a core brings gets jobs killed on the "
                "node, so this should be the memory of a node divided by its cores."
            ],
        )


job_submission_menu = ConsoleMenu(
    this_menu_options=job_submission_menu_options,
    # opened from every menu, so the options of whichever menu that was do not apply
    show_parent_options=False,
    title=JOB_SUBMISSION_MENU_DESCRIPTION.title,
    subtitle=JOB_SUBMISSION_MENU_DESCRIPTION.subtitle,
    prologue_text=JOB_SUBMISSION_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=JOB_SUBMISSION_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=JOB_SUBMISSION_MENU_DESCRIPTION.show_exit_option,
)

job_submission_menu_items = [
    FunctionItem(SEND_JOBS_BY_SIZE, JobSubmissionFunctions.send_jobs_by_size),
    FunctionItem(SWAP_PARTITION, JobSubmissionFunctions.swap_partition),
    FunctionItem(STOP_USING_PARTITION, JobSubmissionFunctions.stop_using_partition),
    FunctionItem(CHANGE_TIME_LIMIT, JobSubmissionFunctions.change_time_limit),
    FunctionItem(CHANGE_MEMORY, JobSubmissionFunctions.change_memory_per_core),
]

add_items_to_menu(job_submission_menu, job_submission_menu_items)
