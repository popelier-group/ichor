"""The job submission options menu, which changes the ``hpc`` block of the ichor config
for the machine ichor is running on: which partitions jobs go to, how long they may run
for, and how much memory a core brings.

It can be opened from every menu by pressing ``j``, as these are settings that tend to
be wanted just before submitting something, from whichever menu that is. Each change is
written to the config file straight away and applies to the next job submitted, so
nothing has to be saved or restarted.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Mapping, MutableMapping, Optional, Union

import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
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

JOB_SUBMISSION_MENU_DESCRIPTION = MenuDescription(
    "Job Submission Options",
    subtitle=(
        "Change which partition jobs are sent to, how long they may run for, and how\n"
        "much memory a core brings. Changes are saved to the config file and apply to\n"
        "the next job submitted.\n"
    ),
)

# the key that opens this menu from any other
JOB_SUBMISSION_MENU_KEY = "j"


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


def format_partitions(ranges: Dict[str, tuple]) -> str:
    """e.g. ``serial [1, 1], multicore [2, 168]``"""

    return ", ".join(f"{name} [{low}, {high}]" for name, (low, high) in ranges.items())


def format_memory(memory) -> str:
    """Memory per core as the prologue shows it, whether one number or one per
    partition."""

    if memory is None:
        return (
            f"not set ({ichor.hpc.global_variables.DEFAULT_MEMORY_PER_CORE_GB} GB "
            "is assumed)"
        )
    if isinstance(memory, Mapping):
        return ", ".join(f"{name} {gb:g} GB" for name, gb in memory.items())

    return f"{memory:g} GB"


def format_walltime(walltime) -> str:
    """The time limit as the prologue shows it."""

    if walltime is None:
        return f"not set ({ichor.hpc.global_variables.DEFAULT_MAX_WALLTIME} is used)"
    if str(walltime).strip().lower() == hpc_settings.NO_WALLTIME:
        return "none (the partition's own limit applies)"

    return str(walltime)


@dataclass
class JobSubmissionMenuOptions(MenuOptions):
    """What the job submission options currently are. These are read from the config
    each time the menu is drawn rather than stored here, as they are the config's to
    keep, and could have been changed by hand since."""

    config_file: str = ""
    machine: str = ""
    partitions: str = ""
    time_limit: str = ""
    memory_per_core: str = ""

    def refresh(self):
        """Reads the current settings out of the config."""

        hpc = current_hpc_block()
        config_path = ichor.hpc.global_variables.ICHOR_CONFIG_PATH

        self.config_file = str(config_path) if config_path else "none found"
        self.machine = ichor.hpc.global_variables.MACHINE or "not in the config"
        self.partitions = (
            format_partitions(hpc_settings.partitions(hpc)) or "none configured"
        )
        self.time_limit = format_walltime(hpc.get("max_walltime"))
        self.memory_per_core = format_memory(hpc.get("memory_per_core_gb"))

    def __call__(self):
        self.refresh()
        return super().__call__()

    def check_can_edit(self) -> Optional[str]:
        """Whether there is a config and a block in it for this machine to change."""

        return cannot_edit_reason()

    def check_partitions(self) -> Optional[str]:
        """Overlapping ranges, and core counts no partition covers."""

        problems = hpc_settings.range_problems(
            hpc_settings.partitions(current_hpc_block())
        )
        return "\n! ".join(problems) or None

    def check_memory_per_partition(self) -> Optional[str]:
        """Partitions with no memory given for them, when memory is per partition.
        Gaussian jobs sent to one cannot be sized and are refused."""

        hpc = current_hpc_block()
        memory = hpc.get("memory_per_core_gb")
        if not isinstance(memory, dict):
            return None

        missing = [name for name in hpc_settings.partitions(hpc) if name not in memory]
        if missing:
            return (
                f"No memory per core is given for {', '.join(missing)}. Use 'Change "
                "the memory per core' to set it."
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


def print_configured_partitions():
    """Lists the partitions in the config, numbered so that one can be chosen."""

    ranges = hpc_settings.partitions(current_hpc_block())
    print("Partitions in the config:")
    if not ranges:
        print("  none")
    for i, (name, (low, high)) in enumerate(ranges.items(), start=1):
        print(f"  {i}. {name}: {low}-{high} cores")
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


def choose_configured_partition(action: str) -> Optional[str]:
    """Asks for one of the configured partitions, by number or by name.

    :return: The partition's name, or None if nothing was chosen.
    """

    ranges = hpc_settings.partitions(current_hpc_block())
    if not ranges:
        print_summary_and_pause(
            "NO PARTITIONS CONFIGURED",
            notes=["Add one with 'Set the partition for a range of core counts'."],
        )
        return None

    print_configured_partitions()
    names = list(ranges)

    while True:
        answer = user_input_free_flow(
            f"Partition to {action} (number or name, enter to cancel): "
        )
        if not answer:
            return None
        answer = answer.strip()
        if answer in ranges:
            return answer
        if answer.isdigit() and 1 <= int(answer) <= len(names):
            return names[int(answer) - 1]
        print(f"{answer} is not one of the partitions above.")


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


def apply_change(
    change: Callable[[MutableMapping], None],
    title: str,
    details: Dict[str, object],
    notes: Optional[List[str]] = None,
):
    """Makes a change to the hpc block in the config file, reloads the config so the
    next job uses it, and says what was done.

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

    problems = hpc_settings.range_problems(hpc_settings.partitions(current_hpc_block()))
    print_summary_and_pause(
        title,
        {**details, "Config file": config_path},
        (notes or [])
        + problems
        + [
            "This applies to the next job submitted. The previous version of the "
            f"config is kept in {hpc_settings.backup_path(config_path).name}."
        ],
    )


class JobSubmissionFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def set_partition():
        """Sends a range of core counts to a partition, e.g. 2-32 cores to
        multicore_small. Partitions whose ranges the new one overlaps have the overlap
        taken out of them (after asking), so each core count has one place to go."""

        if report_cannot_edit():
            return

        print_queue_partitions()
        print_configured_partitions()

        name = user_input_free_flow("Partition name (enter to cancel): ")
        if not name or not name.strip():
            return
        name = name.strip()
        if not confirm_unknown_partition(name):
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

        low_prompt = f" [{default_low}]" if default_low else ""
        low = user_input_int(
            f"Smallest number of cores to send to {name}{low_prompt}: ",
            default_low,
            minimum=1,
        )
        if low is None:
            return
        high_prompt = f" [{default_high}]" if default_high else ""
        high = user_input_int(
            f"Largest number of cores to send to {name}{high_prompt}: ",
            default_high,
            minimum=low,
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
                        f"{low}-{high} cores falls in the middle of {other} "
                        f"[{other_range[0]}, {other_range[1]}], which would split it "
                        f"in two. Change {other}'s range first, so that {low}-{high} "
                        "is at one end of it."
                    ],
                )
                return
            if pieces:
                trims.append((other, other_range, pieces[0]))
            else:
                removals.append((other, other_range))

        knock_on = [
            f"{other} [{old[0]}, {old[1]}] becomes [{new[0]}, {new[1]}]"
            for other, old, new in trims
        ] + [
            f"{other} [{old[0]}, {old[1]}] is removed, as {name} now covers all of it"
            for other, old in removals
        ]
        if knock_on:
            print(f"\n{name} [{low}, {high}] overlaps other partitions, so:")
            for line in knock_on:
                print(f"  {line}")
            if not user_input_bool("Go ahead? (yes/no): ", False):
                return

        memory = hpc.get("memory_per_core_gb")
        partition_memory = None
        if isinstance(memory, dict) and name not in memory:
            suggested = (
                round(on_queue.memory_per_core_gb, 1)
                if on_queue and on_queue.memory_per_core_gb
                else min(memory.values(), default=None)
            )
            suggestion = f" [{suggested}]" if suggested else ""
            partition_memory = user_input_positive_float(
                f"Memory per core on {name}, in GB{suggestion}: ", suggested
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

        details = {"Partition": name, "Cores": f"{low}-{high}"}
        if partition_memory is not None:
            details["Memory per core"] = f"{partition_memory:g} GB"
        apply_change(change, "PARTITION SET", details, knock_on)

    @staticmethod
    def rename_partition():
        """Sends a partition's core counts somewhere else, e.g. multicore to
        multicore_small, keeping the range it covers."""

        old = choose_configured_partition("rename")
        if old is None:
            return

        print_queue_partitions()
        new = user_input_free_flow(f"New name for {old} (enter to cancel): ")
        if not new or not new.strip():
            return
        new = new.strip()
        if not confirm_unknown_partition(new):
            return

        apply_change(
            lambda hpc: hpc_settings.rename_partition(hpc, old, new),
            "PARTITION RENAMED",
            {"Was": old, "Now": new},
        )

    @staticmethod
    def remove_partition():
        """Stops sending jobs to a partition."""

        name = choose_configured_partition("remove")
        if name is None:
            return

        low, high = hpc_settings.partitions(current_hpc_block())[name]
        if not user_input_bool(
            f"Remove {name}? Jobs of {low}-{high} cores will have nowhere to go until "
            "another partition covers them. (yes/no): ",
            False,
        ):
            return

        apply_change(
            lambda hpc: hpc_settings.remove_partition(hpc, name),
            "PARTITION REMOVED",
            {"Partition": name, "Cores it covered": f"{low}-{high}"},
        )

    @staticmethod
    def change_time_limit():
        """Changes how long jobs may run for."""

        if report_cannot_edit():
            return

        current = current_hpc_block().get("max_walltime")
        print(f"Current time limit: {format_walltime(current)}")
        print_queue_partitions()
        print(
            "Write it as days-hours (3-0), hours:minutes:seconds (24:00:00), or "
            f"{hpc_settings.NO_WALLTIME!r} to leave it to the partition.\n"
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
        print(f"Current memory per core: {format_memory(current)}\n")

        per_partition = False
        if len(ranges) > 1:
            per_partition = user_input_bool(
                "Give each partition its own memory per core? (yes/no) "
                f"[{'yes' if isinstance(current, dict) else 'no'}]: ",
                isinstance(current, dict),
            )

        value: Union[float, Dict[str, float]]
        if per_partition:
            value = {}
            for name in ranges:
                on_queue = queue_partition(name)
                if isinstance(current, dict) and name in current:
                    suggested = current[name]
                elif on_queue and on_queue.memory_per_core_gb:
                    suggested = round(on_queue.memory_per_core_gb, 1)
                elif current is not None and not isinstance(current, dict):
                    suggested = current
                else:
                    suggested = None
                suggestion = f" [{suggested}]" if suggested else ""
                gb = user_input_positive_float(
                    f"Memory per core on {name}, in GB{suggestion}: ", suggested
                )
                if gb is None:
                    return
                value[name] = gb
            shown = format_memory(value)
        else:
            suggested = (
                min(current.values(), default=None)
                if isinstance(current, dict)
                else current
            )
            suggestion = f" [{suggested}]" if suggested else ""
            value = user_input_positive_float(
                f"Memory per core, in GB{suggestion}: ", suggested
            )
            if value is None:
                return
            shown = format_memory(value)

        apply_change(
            lambda hpc: hpc_settings.set_memory_per_core_gb(hpc, value),
            "MEMORY PER CORE CHANGED",
            {"Was": format_memory(current), "Now": shown},
            [
                "Asking for more memory than a core brings gets jobs killed on the "
                "node, so this should be what the node really has, divided by its "
                "cores."
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
    FunctionItem(
        "Set the partition for a range of core counts",
        JobSubmissionFunctions.set_partition,
    ),
    FunctionItem("Rename a partition", JobSubmissionFunctions.rename_partition),
    FunctionItem("Remove a partition", JobSubmissionFunctions.remove_partition),
    FunctionItem("Change the time limit", JobSubmissionFunctions.change_time_limit),
    FunctionItem(
        "Change the memory per core", JobSubmissionFunctions.change_memory_per_core
    ),
]

add_items_to_menu(job_submission_menu, job_submission_menu_items)
