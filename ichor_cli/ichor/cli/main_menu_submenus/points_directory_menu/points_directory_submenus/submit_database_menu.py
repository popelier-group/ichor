"""The menu which processes the finished calculations of a PointsDirectory: it collects
the Gaussian and AIMAll results of every point into one database, and then turns that
database into the per-atom csv files that the dataset preparation and training stages
read.

The two stages are one menu because a database on its own is not what any later stage
reads. On a compute node they are two jobs, the second held on the first, so the csv job
is given a database which does not exist yet at the time both are submitted.

The setting which most often goes wrong here is the number of cores, as the database job
has no use for the cores themselves but the batch system hands out memory per core, so a
job left at one core is a job given one core's worth of memory. It is therefore worked out
from the size of the selected PointsDirectory (see :func:`suggest_number_of_cores`) rather
than being left at a fixed default.
"""

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Union

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    format_memory_gb,
    job_memory_gb,
    maximum_cores,
    memory_per_core_gb,
    print_summary_and_pause,
    user_input_bool,
    user_input_int,
    user_input_path,
    user_input_restricted,
)
from ichor.core.database.query_database import (
    get_alf_from_first_db_geometry,
    write_processed_data_for_atoms_parallel,
)
from ichor.core.files import PointsDirectory, PointsDirectoryParent
from ichor.core.files.aimall import IntDirectory
from ichor.core.files.point_directory import PointDirectory
from ichor.core.useful_functions import single_or_many_points_directories
from ichor.hpc.main.database import (
    AVAILABLE_DATABASE_FORMATS,
    database_name,
    database_path,
    processed_csvs_directory,
    submit_make_database,
    submit_make_database_and_csvs,
)

SUBMIT_DATABASE_MENU_DESCRIPTION = MenuDescription(
    "Process Point Calculations",
    subtitle="Use this menu to collect the finished Gaussian and AIMAll calculations of "
    "a PointsDirectory into a database, and to turn that database into the csv files "
    "that model training reads.\n",
)

# TODO: possibly make this be read from a file
SUBMIT_DATABASE_MENU_DEFAULTS = {
    "default_database_format": "sqlite",
    "default_ncores": 1,
    "default_run_on_compute_node": True,
    # the csv files are what the training stages actually read, and a database is not
    # much use without them, so they are made straight after the database by default
    "default_make_csv_files": True,
    # the csv job works out one atom per core, so this follows the number of atoms in the
    # system once one has been measured
    "default_csv_ncores": 4,
    "default_rotate_multipole_moments": True,
    "default_calculate_feature_forces": False,
}

# The whole database is written out to the csv files: the integration error and IQA/wfn
# energy difference filters are set high enough to keep every point, so the filtering of
# bad points is left to the dataset preparation stage.
FLOAT_INTEGRATION_ERROR = 100000000.0
FLOAT_DIFFERENCE_IQA_WFN = 10000000.0

# The memory the job needs is worked out from what making a database actually holds at
# once. The points are read one at a time and given back as soon as they are in the
# database (see `AnnotatedDirectory.unload`), so what has to fit is the parsed contents of
# a single point rather than of the whole PointsDirectory.
#
# What is left behind for every point is the PointDirectory itself: the paths of its
# Gaussian/AIMAll files and an unread file object for each of them. Measured at ~7.4 KB
# per point, rounded up here.
BYTES_HELD_PER_POINT = 8_000
# The files of one point which the database reads (its .wfn, the .int file of every atom,
# and the geometry) turn into python objects of roughly the size of the text they came
# from: 75 KB in memory was measured against 98 KB of .wfn and .int files, as the .wfn
# primitive coefficients inflate while the .int tables shrink to the handful of numbers
# taken out of them. Rounded up to leave room for a system whose .wfn dominates.
PARSED_POINT_INFLATION = 1.5
# A json database holds the data of a whole chunk of points before writing the chunk out
# (npoints_per_json in `PointsDirectory.write_to_json_database`), rather than one point at
# a time as sqlite does.
JSON_POINTS_HELD = 500
# What that data takes for one point, as a multiple of the size of its .int files, which
# is where nearly all of it comes from. 57 KB was measured against 92 KB of .int files, so
# this is on the safe side of what was seen.
JSON_DATA_INFLATION = 1.0
# What the job costs before it has read anything: the interpreter, the imports (numpy,
# pandas, SQLAlchemy), the database session and what sqlite buffers.
BASE_MEMORY_GB = 0.5
# The share of the job's memory the estimate is allowed to fill. The rest covers what is
# not worth modelling, e.g. the fragmentation of the many small objects a point is parsed
# into and however much the batch system counts on top of what python asks for.
MEMORY_FRACTION = 0.7
# How many point directories are measured to work out what one point costs. They are all
# the same system with the same number of atoms, so a handful is enough; measuring every
# one of them would mean a stat of every file of every point on a networked filesystem.
SAMPLED_POINTS = 5
# The files of a point which are read into the database. The rest of what AIMAll leaves
# behind (.sumviz and .mgpviz in particular, which are the largest files there) is never
# read, so counting it would put the estimate out by an order of magnitude.
FILES_READ_INTO_DATABASE = {".wfn", ".xyz", ".gjf"}


def points_directories_in(points_directory_path: Path) -> List[Path]:
    """Returns the PointsDirectory-ies the selected path holds, which is the path itself
    unless it is a parent to many of them.

    :param points_directory_path: The selected PointsDirectory or parent to
        PointsDirectory-ies.
    """

    if not single_or_many_points_directories(points_directory_path):
        return [points_directory_path]

    return [d for d in points_directory_path.iterdir() if PointsDirectory.check_path(d)]


def measure_point_directory(point_path: Path) -> Tuple[int, int, int]:
    """Returns how many bytes of one point directory the database reads, how many of those
    are its .int files, and how many atoms the system has.

    :param point_path: The path of the point directory (a ``.pointdir``).
    :return: (the bytes of the files which are read, the bytes of the .int files, the
        number of atoms).
    """

    read_bytes = 0
    int_file_bytes = 0
    natoms = 0

    for f in point_path.iterdir():
        if f.is_file() and f.suffix in FILES_READ_INTO_DATABASE:
            read_bytes += f.stat().st_size
        # the AIMAll output of every atom, which is where most of what is read comes from
        elif f.is_dir() and IntDirectory.check_path(f):
            int_files = [i for i in f.iterdir() if i.suffix == ".int"]
            int_file_bytes += sum(i.stat().st_size for i in int_files)
            # AIMAll writes one .int file per atom, so this is the number of atoms in the
            # system, which is the number of cores the csv stage has any use for
            natoms = max(natoms, len(int_files))

    return read_bytes + int_file_bytes, int_file_bytes, natoms


def measure_points_directory(points_directory_path: Path) -> Tuple[int, int, int, int]:
    """Counts the points in the selected directory and measures a few of them, which is
    what the memory the job needs is estimated from (see :func:`estimated_memory_gb`).

    Only the count walks the whole directory, and it only lists directories rather than
    looking inside them, so this stays quick on a PointsDirectory of many thousands of
    points on a networked filesystem.

    :param points_directory_path: The selected PointsDirectory or parent to
        PointsDirectory-ies.
    :return: (the number of points, the bytes of the largest point measured, the bytes of
        the .int files of the largest point measured, the number of atoms in the system).
        All 0 if the directory could not be read, which the menu checks warn about.
    """

    npoints = 0
    read_bytes = 0
    int_file_bytes = 0
    natoms = 0

    try:
        for pointsdir in points_directories_in(points_directory_path):
            for point_path in pointsdir.iterdir():
                if not PointDirectory.check_path(point_path):
                    continue
                npoints += 1
                # the points of one system are all much the same size, so the first few
                # say what one point costs; the largest of them is the one to go by
                if npoints <= SAMPLED_POINTS:
                    point_read, point_ints, point_atoms = measure_point_directory(
                        point_path
                    )
                    read_bytes = max(read_bytes, point_read)
                    int_file_bytes = max(int_file_bytes, point_ints)
                    natoms = max(natoms, point_atoms)
    except OSError:
        # a path which cannot be read (it does not exist, or is not a PointsDirectory) is
        # caught by the check functions, which say so in the menu prologue
        return 0, 0, 0, 0

    return npoints, read_bytes, int_file_bytes, natoms


def estimated_memory_gb(
    npoints: int,
    point_read_bytes: int,
    int_file_bytes: int,
    database_format: str,
) -> float:
    """Returns the memory (in GB) making the database is estimated to need.

    :param npoints: The number of points going into the database.
    :param point_read_bytes: The bytes of one point which are read into the database.
    :param int_file_bytes: The bytes of the .int files of one point.
    :param database_format: The format the database is written in, sqlite or json.
    """

    # every point leaves its (unread) file objects behind for the whole run, which is the
    # only part of the estimate that grows with the number of points
    memory_bytes = npoints * BYTES_HELD_PER_POINT
    # and one point at a time is held with its files read in
    memory_bytes += PARSED_POINT_INFLATION * point_read_bytes

    # a json database holds a chunk of points' worth of data before writing it out
    if database_format == "json":
        memory_bytes += JSON_POINTS_HELD * JSON_DATA_INFLATION * int_file_bytes

    return BASE_MEMORY_GB + memory_bytes / 1024**3


def cores_needed_for(memory_gb: float) -> int:
    """Returns the number of cores whose memory would hold the given estimate, as the
    batch system hands out memory per core and the job has no other use for them.

    :param memory_gb: The memory the job is estimated to need.
    """

    per_core_gb = MEMORY_FRACTION * memory_per_core_gb()

    return max(1, math.ceil(memory_gb / per_core_gb))


def make_csvs_on_login_node(db_path: Path, db_type: str, ncores: int) -> Path:
    """Makes the csv files of a database here and now rather than on a compute node, which
    is what a database made on the login node is followed by.

    The database is finished by the time this is called, so the ALF can simply be read
    from it (the compute node job has to read it once it starts instead, as it is
    submitted before the database exists).

    :param db_path: The database to read.
    :param db_type: The type of database, sqlite or json.
    :param ncores: The number of cores to work the atoms out over.
    :return: The directory the csv files were written to.
    """

    csvs_path = processed_csvs_directory(db_path)
    alf = get_alf_from_first_db_geometry(db_path, db_type)

    write_processed_data_for_atoms_parallel(
        db_path,
        db_type,
        alf,
        ncores,
        max_diff_iqa_wfn=FLOAT_DIFFERENCE_IQA_WFN,
        max_integration_error=FLOAT_INTEGRATION_ERROR,
        calc_multipoles=submit_database_menu_options.selected_rotate_multipole_moments,
        calc_forces=submit_database_menu_options.selected_calculate_feature_forces,
        parent_directory=csvs_path,
    )

    return csvs_path


def suggest_csv_number_of_cores() -> int:
    """Returns the number of cores to suggest for the csv job which follows the database
    job.

    That job works out one atom at a time, one atom per core, so the number of atoms in
    the system is the most it has any use for and is what is suggested. The atoms are
    counted from the .int files of a point when the PointsDirectory is selected; when that
    is not known, the menu default is kept.
    """

    if not number_of_atoms:
        return SUBMIT_DATABASE_MENU_DEFAULTS["default_csv_ncores"]

    largest = maximum_cores()

    return min(number_of_atoms, largest) if largest else number_of_atoms


def suggest_number_of_cores(
    npoints: int,
    point_read_bytes: int,
    int_file_bytes: int,
    database_format: str,
) -> int:
    """Returns the number of cores to ask for, which is the number the memory of the job
    has to come from (see :func:`cores_needed_for`). It is held to the most a job can ask
    for on this machine, as a job asking for more than that is simply refused.

    :param npoints: The number of points going into the database. If this is not known
        (0), the menu default is returned instead.
    :param point_read_bytes: The bytes of one point which are read into the database.
    :param int_file_bytes: The bytes of the .int files of one point.
    :param database_format: The format the database is written in, sqlite or json.
    """

    if npoints <= 0:
        return SUBMIT_DATABASE_MENU_DEFAULTS["default_ncores"]

    needed = cores_needed_for(
        estimated_memory_gb(npoints, point_read_bytes, int_file_bytes, database_format)
    )
    largest = maximum_cores()

    return min(needed, largest) if largest else needed


# dataclass used to store values for SubmitAIMALLMenu
@dataclass
class SubmitDatabaseMenuOptions(MenuOptions):

    selected_database_format: str
    selected_number_of_cores: int
    selected_run_on_compute_node: bool
    # whether the csv files are made from the database as soon as it is written
    selected_make_csv_files: bool
    # the cores the csv job asks for, which it works the atoms out over
    selected_csv_number_of_cores: int
    # settings of the csv files: whether the multipole moments of each atom are rotated
    # into its own frame, and whether the forces are given in feature coordinates
    selected_rotate_multipole_moments: bool
    selected_calculate_feature_forces: bool
    # defaults to the current working directory
    selected_points_directory_path: Path = field(default_factory=lambda: Path.cwd())
    # the points in the selected directory, counted when it is selected so that the memory
    # the job needs (and so the cores it has to ask for) can be worked out from it.
    # 0 = not known
    number_of_points_in_directory: int = 0

    def check_path(self):

        pd_path = Path(self.selected_points_directory_path)
        if not pd_path.is_dir():
            return "Current path is not a directory."

    def check_selected_points_directory_path(self) -> Union[str, None]:
        """Checks whether the given PointsDirectory exists or if it is a directory."""
        pd_path = Path(self.selected_points_directory_path)
        if (pd_path.suffix != PointsDirectory._suffix) and (
            pd_path.suffix != PointsDirectoryParent._suffix
        ):
            return f"Current path: {pd_path} might not be PointsDirectory-like)."

    def check_selected_number_of_cores(self) -> Union[str, None]:
        """Checks that the job asks for at least one core."""
        if self.selected_number_of_cores < 1:
            return (
                f"Current number of cores: {self.selected_number_of_cores} "
                "must be 1 or greater."
            )

    def check_number_of_cores_fits_machine(self) -> Union[str, None]:
        """Checks the job does not ask for more cores than the machine can give it."""
        largest = maximum_cores()
        if largest and self.selected_number_of_cores > largest:
            return (
                f"Current number of cores: {self.selected_number_of_cores:,} is more "
                f"than the {largest:,} a job can ask for on this machine."
            )

    def check_selected_csv_number_of_cores(self) -> Union[str, None]:
        """Checks the csv job asks for at least one core, no more than the machine can
        give it, and no more than it has atoms to work out over."""
        if not self.selected_make_csv_files:
            return None

        ncores = self.selected_csv_number_of_cores
        if ncores < 1:
            return f"Current csv job cores: {ncores} must be 1 or greater."

        largest = maximum_cores()
        if largest and ncores > largest:
            return (
                f"Current csv job cores: {ncores:,} is more than the {largest:,} a job "
                f"can ask for on this machine."
            )

        if number_of_atoms and ncores > number_of_atoms:
            return (
                f"Current csv job cores: {ncores:,} is more than the "
                f"{number_of_atoms:,} atoms in the system. The job works out one atom "
                f"per core, so the rest would sit idle."
            )

    def check_points_directory_fits_in_memory(self) -> Union[str, None]:
        """Checks that what making the database holds fits in the memory of the job.

        The job makes no use of the cores it asks for, as it reads the points one after
        another, but the batch system hands out memory per core, so the cores are how it
        is given the memory it needs."""
        npoints = self.number_of_points_in_directory
        if not npoints or self.selected_number_of_cores < 1:
            return None

        ncores = self.selected_number_of_cores
        needed_gb = estimated_memory_gb(
            npoints,
            sampled_point_read_bytes,
            sampled_int_file_bytes,
            self.selected_database_format,
        )
        if needed_gb <= MEMORY_FRACTION * job_memory_gb(ncores):
            return None

        needed_cores = cores_needed_for(needed_gb)
        largest = maximum_cores()
        if largest and needed_cores > largest:
            way_out = (
                f"That would need {needed_cores:,} cores, more than the {largest:,} a "
                f"job can ask for on this machine, so the points have to be split into "
                f"several PointsDirectory-ies (the database can then be made from the "
                f"parent directory holding them)."
            )
        else:
            way_out = f"Ask for {needed_cores:,} cores."

        return (
            f"The {npoints:,} points are estimated to need "
            f"{format_memory_gb(needed_gb)}, which is more than a {ncores} core job is "
            f"given ({job_memory_gb(ncores):,.0f} GB, of which the estimate is allowed "
            f"{MEMORY_FRACTION:.0%}), so the job may be killed for running out of "
            f"memory. {way_out}"
        )


# initialize dataclass for storing information for menu
submit_database_menu_options = SubmitDatabaseMenuOptions(
    *SUBMIT_DATABASE_MENU_DEFAULTS.values()
)

# what the selected PointsDirectory was measured to hold, which the memory estimate is
# worked out from (see `measure_points_directory`). 0 = nothing measured yet
sampled_point_read_bytes = 0
sampled_int_file_bytes = 0
# the atoms in the system, which is the number of cores the csv job that follows the
# database job has any use for, as that job is parallelised one atom per core. 0 = unknown
number_of_atoms = 0

# the number of cores follows the size of the PointsDirectory unless the user picks one by
# hand, in which case their choice is kept even when a different PointsDirectory (or a
# different database format) is selected
ncores_overridden = False
# the same for the cores of the csv job, which follow the number of atoms in the system
csv_ncores_overridden = False


def derive_number_of_cores():
    """Sets the number of cores from the size of the selected PointsDirectory and the
    format the database is written in, unless the user has picked a number by hand. Both
    of those can change while the menu is open, which is why this is done in one place.
    """

    if ncores_overridden:
        return

    submit_database_menu_options.selected_number_of_cores = suggest_number_of_cores(
        submit_database_menu_options.number_of_points_in_directory,
        sampled_point_read_bytes,
        sampled_int_file_bytes,
        submit_database_menu_options.selected_database_format,
    )


def derive_csv_number_of_cores():
    """Sets the cores of the csv job from the number of atoms in the selected
    PointsDirectory, unless the user has picked a number by hand."""

    if csv_ncores_overridden:
        return

    submit_database_menu_options.selected_csv_number_of_cores = (
        suggest_csv_number_of_cores()
    )


def update_points_directory_information(points_directory_path: Path) -> int:
    """Measures the newly selected PointsDirectory (without reading any of its points in)
    and, unless the number of cores was picked by hand, derives that from it.

    :param points_directory_path: The PointsDirectory (or parent to PointsDirectory-ies)
        that was selected.
    :return: The number of points counted (0 if the directory could not be read).
    """
    global sampled_point_read_bytes, sampled_int_file_bytes, number_of_atoms

    (
        npoints,
        sampled_point_read_bytes,
        sampled_int_file_bytes,
        number_of_atoms,
    ) = measure_points_directory(Path(points_directory_path))

    submit_database_menu_options.number_of_points_in_directory = npoints
    derive_number_of_cores()
    derive_csv_number_of_cores()

    return npoints


# class with static methods for each menu item that calls a function.
class SubmitDatabaseFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_points_directory():
        """Asks user to update points directory and then updates PointsDirectoryMenuOptions instance."""
        pd_path = user_input_path(
            "Path to the PointsDirectory (or to a directory holding several): "
        )
        ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH = Path(
            pd_path
        ).absolute()
        submit_database_menu_options.selected_points_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
        )
        # the memory the job needs (and so the number of cores it has to ask for to be
        # given that memory) follows the size of the PointsDirectory
        update_points_directory_information(
            ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
        )

    @staticmethod
    def select_database():
        """Asks user to update the method for AIMALL. The method
        needs to be added to the WFN file so that AIMALL does the correct
        calculation."""

        submit_database_menu_options.selected_database_format = user_input_restricted(
            AVAILABLE_DATABASE_FORMATS.keys(),
            "Database format (sqlite or json): ",
            submit_database_menu_options.selected_database_format,
        )
        # a json database holds a chunk of points at a time rather than one point, so it
        # needs more memory than an sqlite one made from the same PointsDirectory
        derive_number_of_cores()

    @staticmethod
    def select_number_of_cores():
        """Asks user to select number of cores.

        The job itself is not parallel: it reads the points one after another. The cores
        are asked for because the batch system hands out memory per core, so they are how
        the job is given enough memory to hold a point (and the file objects of the points
        it has already been through) without being killed.

        The number the PointsDirectory needs is suggested (see
        :func:`suggest_number_of_cores`) and is what the menu keeps it at as a
        PointsDirectory or a format is selected. Entering a number here pins it instead;
        entering 0 goes back to following the PointsDirectory."""
        global ncores_overridden

        npoints = submit_database_menu_options.number_of_points_in_directory
        suggested = suggest_number_of_cores(
            npoints,
            sampled_point_read_bytes,
            sampled_int_file_bytes,
            submit_database_menu_options.selected_database_format,
        )

        # one short line each, as this is printed just above the prompt
        if npoints:
            needed_gb = estimated_memory_gb(
                npoints,
                sampled_point_read_bytes,
                sampled_int_file_bytes,
                submit_database_menu_options.selected_database_format,
            )
            print(f"\n{npoints:,} points, needing {format_memory_gb(needed_gb)}.")
            print(
                f"Suggested: {suggested:,} core{'' if suggested == 1 else 's'}, at "
                f"{memory_per_core_gb()} GB per core on this machine."
            )
            print("Points are read one at a time: cores buy memory, not speed.")
            if number_of_atoms:
                print(
                    f"The csv job which follows takes one core per atom "
                    f"({number_of_atoms:,}).\n"
                )
            else:
                print("")
        else:
            print("\nNo PointsDirectory has been measured yet (select one above),")
            print("so the memory the job needs is not known.\n")

        ncores = user_input_int(
            "Cores for the database job (0 = as many as its memory needs): ",
            submit_database_menu_options.selected_number_of_cores,
            minimum=0,
        )

        # 0 hands the setting back to the PointsDirectory, anything else pins it
        if not ncores:
            ncores_overridden = False
            derive_number_of_cores()
            return

        ncores_overridden = True
        submit_database_menu_options.selected_number_of_cores = ncores

    @staticmethod
    def select_csv_number_of_cores():
        """Asks user to select the number of cores for the csv job.

        That job is parallel for real: it works out one atom per core, so cores up to the
        number of atoms in the system make it faster and any beyond that sit idle.

        The number of atoms is suggested and is what the menu keeps it at as a
        PointsDirectory is selected. Entering a number here pins it instead; entering 0
        goes back to following the number of atoms."""
        global csv_ncores_overridden

        suggested = suggest_csv_number_of_cores()
        largest = maximum_cores()

        # one short line each, as this is printed just above the prompt
        if number_of_atoms:
            print(f"\n{number_of_atoms:,} atoms, so one core each is {suggested:,}.")
            print("Atoms are worked out one per core: fewer cores are slower,")
            print("cores past the atom count sit idle.")
            if largest and number_of_atoms > largest:
                print(f"This machine allows {largest:,} cores, fewer than the atoms.\n")
            else:
                print("")
        else:
            print("\nNo PointsDirectory has been measured yet (select one above),")
            print("so the number of atoms is not known.\n")

        ncores = user_input_int(
            "Cores for the csv job (0 = one per atom): ",
            submit_database_menu_options.selected_csv_number_of_cores,
            minimum=0,
        )

        # 0 hands the setting back to the number of atoms, anything else pins it
        if not ncores:
            csv_ncores_overridden = False
            derive_csv_number_of_cores()
            return

        csv_ncores_overridden = True
        submit_database_menu_options.selected_csv_number_of_cores = ncores

    @staticmethod
    def select_run_on_compute_node():
        """
        Asks user whether or not to submit database making on compute.
        """

        submit_database_menu_options.selected_run_on_compute_node = user_input_bool(
            "Run on a compute node, rather than here on the login node (yes/no): ",
            submit_database_menu_options.selected_run_on_compute_node,
        )

    @staticmethod
    def select_make_csv_files():
        """Asks whether the csv files are made from the database as soon as it is written.

        A database on its own is not what any of the training stages read, so this is on
        by default. On a compute node the csvs are made by a second job held on the
        database job, which is how it is given a database that does not exist yet at the
        time both are submitted."""

        submit_database_menu_options.selected_make_csv_files = user_input_bool(
            "Make the csv files from the database as well (yes/no): ",
            submit_database_menu_options.selected_make_csv_files,
        )

    @staticmethod
    def select_rotate_multipole_moments():
        """Asks whether the multipole moments written to the csv files are rotated from
        the global frame into the local frame of each atom, which is the frame a model
        predicts them in."""

        submit_database_menu_options.selected_rotate_multipole_moments = (
            user_input_bool(
                "Rotate multipole moments into each atom's own frame (yes/no): ",
                submit_database_menu_options.selected_rotate_multipole_moments,
            )
        )

    @staticmethod
    def select_calculate_feature_forces():
        """Asks whether the forces are worked out in feature coordinates and written to
        the csv files alongside the properties."""

        submit_database_menu_options.selected_calculate_feature_forces = (
            user_input_bool(
                "Calculate forces in feature coordinates (yes/no): ",
                submit_database_menu_options.selected_calculate_feature_forces,
            )
        )

    @staticmethod
    def points_directory_to_database():
        """Converts the current given PointsDirectory to a SQLite3 database. Can be submitted on compute
        and works for one `PointsDirectory` or parent directory containing many `PointsDirectory`-ies

        Unless it is turned off, the csv files are made from the database as well: on a
        compute node by a second job held on this one, and here and now when the database
        is being made on the login node.
        """

        is_parent_directory_to_many_points_directories = (
            single_or_many_points_directories(
                ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
            )
        )

        database_format, ncores, run_on_compute_node = (
            submit_database_menu_options.selected_database_format,
            submit_database_menu_options.selected_number_of_cores,
            submit_database_menu_options.selected_run_on_compute_node,
        )

        # this is used to be able to call the respective methods from PointsDirectory
        # so that the same code below is used with the respective methods
        str_database_method = AVAILABLE_DATABASE_FORMATS[database_format]

        points_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
        )
        contents = (
            "many PointsDirectory-ies"
            if is_parent_directory_to_many_points_directories
            else "one PointsDirectory"
        )
        # the database is written next to the PointsDirectory, so that it is not a single
        # file among thousands of point directories named after the same system
        db_path = database_path(points_directory_path, database_format)
        # the name the write methods are given, which they add the suffix of the format to
        db_name = str(
            points_directory_path.parent / database_name(points_directory_path)
        )
        npoints = submit_database_menu_options.number_of_points_in_directory

        make_csv_files = submit_database_menu_options.selected_make_csv_files
        csv_ncores = submit_database_menu_options.selected_csv_number_of_cores
        csvs_path = processed_csvs_directory(db_path)
        rotate_multipole_moments = (
            submit_database_menu_options.selected_rotate_multipole_moments
        )
        calculate_feature_forces = (
            submit_database_menu_options.selected_calculate_feature_forces
        )

        if run_on_compute_node:

            if make_csv_files:
                # the csv job is held on the database job by the batch system, so it
                # starts as soon as the database has been written and nothing about the
                # database is read here, where it does not exist yet
                job_id, csvs_job_id = submit_make_database_and_csvs(
                    points_directory_path,
                    database_format,
                    ncores=ncores,
                    csv_ncores=csv_ncores,
                    float_difference_iqa_wfn=FLOAT_DIFFERENCE_IQA_WFN,
                    float_integration_error=FLOAT_INTEGRATION_ERROR,
                    rotate_multipole_moments=rotate_multipole_moments,
                    calculate_feature_forces=calculate_feature_forces,
                )
            else:
                job_id, csvs_job_id = (
                    submit_make_database(
                        points_directory_path,
                        database_format,
                        ncores=ncores,
                    ),
                    None,
                )

            # remember the database that was asked for, so that anything else which
            # works from a database starts from this one
            ichor.cli.global_menu_variables.SELECTED_DATABASE_PATH = db_path

            summary = {
                "PointsDirectory": points_directory_path,
                "Contents": contents,
                "Points": f"{npoints:,}" if npoints else "not counted",
                "Database format": database_format,
                "Database": db_path,
                "Job ID": job_id.id if job_id else "not available",
                "CPU cores": f"{ncores} ({job_memory_gb(ncores):,.0f} GB of memory)",
                "Ran on": "compute node",
            }
            notes = [
                "The database collects the geometries and the Gaussian/AIMAll "
                "results of every point into one place, so it is worth running "
                "only once those calculations have finished; any point missing "
                "data is reported in the job's output.",
                "The job is now queued, so it will not start immediately and this "
                "menu does not wait for it. Check on it with your batch system's "
                "queue command (e.g. qstat / squeue).",
                "The database is written next to the PointsDirectory (not inside "
                "it) and named after it.",
                "The database job reads the points one at a time, so the cores it "
                "asks for do not make it faster: they are how it is given the "
                "memory it needs, which is why the number follows the size of the "
                "PointsDirectory.",
            ]

            if make_csv_files:
                summary["csv folder"] = csvs_path
                summary["csv job ID"] = (
                    csvs_job_id.id if csvs_job_id else "not available"
                )
                summary["csv CPU cores"] = (
                    f"{csv_ncores} (one atom per core)"
                    if number_of_atoms
                    else f"{csv_ncores}"
                )
                notes.append(
                    "The csv files are made by a second job which is held on the first "
                    "one, so both are in the queue now and the csvs are written as soon "
                    "as the database is finished. They land next to the database, and "
                    "are what the dataset preparation menu is then pointed at."
                )
                notes.append(
                    "The csv job works out one atom per core, and writes out every "
                    "point in the database: the filtering of bad points is done by the "
                    "dataset preparation menu, which is what the csv folder is then "
                    "given to."
                )
            else:
                notes.append(
                    "The csv files were not asked for, so the database is not yet in a "
                    "form any of the training stages read. Turning 'make csv files' on "
                    "and running this again is what makes them."
                )

            print_summary_and_pause("DATABASE JOB SUBMITTED", summary, notes)
            return

        # pointsdirectory parent json on login
        if is_parent_directory_to_many_points_directories:
            pointsdirparent = PointsDirectoryParent(points_directory_path)
            func = getattr(pointsdirparent, str_database_method)
            # written to the same place as the compute node job would write it, rather
            # than to the default of the write method, which is wherever ichor was
            # started from
            database_written_path = func(db_name, print_missing_data=True)
        else:
            pointdir = PointsDirectory(points_directory_path)
            func = getattr(pointdir, str_database_method)
            database_written_path = func(db_name, print_missing_data=True)

        ichor.cli.global_menu_variables.SELECTED_DATABASE_PATH = db_path

        summary = {
            "PointsDirectory": points_directory_path,
            "Contents": contents,
            "Points": f"{npoints:,}" if npoints else "not counted",
            "Database format": database_format,
            "Database": database_written_path if database_written_path else db_path,
            "Ran on": "login node (not submitted)",
        }
        notes = [
            "The database was made here and now rather than on a compute node, so "
            "it is already finished. Any point that was missing Gaussian or AIMAll "
            "data is listed above.",
            "It is written next to the PointsDirectory, not inside it.",
        ]

        if make_csv_files:
            # the database is finished, so the csvs can simply be made after it rather
            # than by a job held on anything
            written_csvs_path = make_csvs_on_login_node(
                Path(database_written_path) if database_written_path else db_path,
                database_format,
                csv_ncores,
            )
            summary["csv folder"] = written_csvs_path
            summary["csv CPU cores"] = csv_ncores
            notes.append(
                "The csv files were made from it straight afterwards and written next "
                "to it, so they are ready for the dataset preparation menu."
            )
        else:
            notes.append(
                "The csv files were not asked for, so the database is not yet in a form "
                "any of the training stages read. Turning 'make csv files' on and "
                "running this again is what makes them."
            )

        print_summary_and_pause("DATABASE WRITTEN", summary, notes)


# make menu items
# can use lambda functions to change text of options as well :)
submit_database_menu_items = [
    FunctionItem(
        "Select the PointsDirectory to process",
        SubmitDatabaseFunctions.select_points_directory,
    ),
    FunctionItem(
        "Set the database format (sqlite or json)",
        SubmitDatabaseFunctions.select_database,
    ),
    FunctionItem(
        "Set the number cores for the database job (memory allocation)",
        SubmitDatabaseFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Run on a compute node, or here on the login node",
        SubmitDatabaseFunctions.select_run_on_compute_node,
    ),
    FunctionItem(
        "Create training data files (csv)",
        SubmitDatabaseFunctions.select_make_csv_files,
    ),
    FunctionItem(
        "Set the number of cores for the csv job (one core per atom)",
        SubmitDatabaseFunctions.select_csv_number_of_cores,
    ),
    FunctionItem(
        "Rotate multipole moments into each atom's frame (csv files)",
        SubmitDatabaseFunctions.select_rotate_multipole_moments,
    ),
    FunctionItem(
        "Calculate forces in feature coordinates (csv files)",
        SubmitDatabaseFunctions.select_calculate_feature_forces,
    ),
    FunctionItem(
        "Run: make the database and training csv files",
        SubmitDatabaseFunctions.points_directory_to_database,
    ),
]

# initialize menu
submit_database_menu = ConsoleMenu(
    this_menu_options=submit_database_menu_options,
    title=SUBMIT_DATABASE_MENU_DESCRIPTION.title,
    subtitle=SUBMIT_DATABASE_MENU_DESCRIPTION.subtitle,
    prologue_text=SUBMIT_DATABASE_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=SUBMIT_DATABASE_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=SUBMIT_DATABASE_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(submit_database_menu, submit_database_menu_items)
