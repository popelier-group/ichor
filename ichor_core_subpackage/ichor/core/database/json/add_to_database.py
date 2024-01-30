# TODO: make this more robust as some data might be absent. Check that .wfn exists before adding wfn data
# TODO: check that gaussian out forces exist. Check that int file exists.
# TODO: move this to PointDirectory, where the return dict depends on the classes which are used as files
import warnings
from datetime import datetime


def get_data_for_point(
    point: "PointDirectory",  # noqa F821,
    print_missing_data=True,
):
    """Returns all information for a point

    :param database_path: Path to database
    :param point: A PointDirectory instance, containing Gaussian/AIMAll outputs that can be
        written to the database.

    .. note:: Even if atomic data (.int file) is missing for a particular atom in the system,
        the information for the point will still be added to the database. This is because
        the rest the point can still be used in the training set for the other atoms.
    """

    # check for .sh file in directory as AIMALL should delete it if it ran successfully
    # if .sh file is found then do not append this point to the database as it can cause problems
    # when reading the database

    point_dict = {}
    point_dict["name"] = point.name_without_suffix

    for _f in point.path.iterdir():
        if _f.suffix == ".sh":
            print(
                f"A shell file (.sh) was found in {point.path.absolute()}, so AIMAll probably crashed. Not added to db."
            )
            return

    ###############################
    # wfn information
    ###############################

    # if wfn file exists
    if point.wfn:
        point_dict["date_added"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        point_dict["wfn_energy"] = point.wfn.total_energy

    # if file does not exist, still add to database, but do not contain wfn information
    else:
        point_dict["date_added"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        point_dict["wfn_energy"] = None

        if print_missing_data:
            print(
                f"Point {point.path} does not contain a Gaussian wavefunction (.wfn) file."
            )

    ###############################
    # gaussian output file check
    ###############################

    if not point.gaussian_output:
        if print_missing_data:
            print(f"Point {point.path} does not contain a Gaussian output (.gau) file.")

    ###############################
    # _atomicfiles directory check
    ###############################

    if not point.ints:

        if print_missing_data:
            print(
                f"Point {point.path} does not contain an atomicfiles directory (containing AIMAll .int)."
            )

    missing_int_files = []

    point_dict["atomic_data"] = {}

    # add information to dataset table for each atom
    for atom_name in point.atom_names:

        point_dict["atomic_data"][atom_name] = {}
        point_dict_atomic = point_dict["atomic_data"][atom_name]

        point_dict_atomic["coordinates"] = point[atom_name].coordinates.tolist()

        ###############################
        # .gau / gaussian output information
        ###############################

        # forces are saved directly from gaussian out file, thus they are in
        # global cartesian coordinates. This means these forces need to be rotated later
        # when an ALF is chosen for atoms.
        if point.gaussian_output:
            if point.gaussian_output.global_forces:
                point_dict_atomic["global_forces"] = list(
                    point.gaussian_output.global_forces[atom_name]
                )

            # in case that the force keyword was not used but gaussian out exists
            else:
                print(
                    f"Point {point.path} does not have forces in Gaussian output (.gau) file."
                )
                point_dict_atomic["global_forces"] = [None, None, None]
        # in case that gaussian out does not exist in point directory
        else:
            point_dict_atomic["global_forces"] = [None, None, None]

        ###############################
        # .int file information
        ###############################
        if point.ints:
            # add information from int file for the current atom
            # get the INT instance representing the .int file for the atom
            # use get here to get a default value of None if .int file is missing for some atom
            atom_int_file = point.ints.get(atom_name, None)

            # if .int file / INT instance exists, then data can be read in
            if atom_int_file:

                # do not display warning from .int file if iqa energy is not there
                # iqa energy will not be in an existing .int file in -encomp setting is below 3
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore")
                    point_dict_atomic["iqa"] = atom_int_file.iqa

                point_dict_atomic["integration_error"] = atom_int_file.integration_error

                # note that these are not rotated because the alf has not been chosen yet
                # the user can choose an alf and rotate the global spherical multipoles as needed
                point_dict_atomic[
                    "global_spherical_multipole_moments"
                ] = atom_int_file.global_spherical_multipoles

            # if .int file for an atom does not exist then (but _atomicfiles directory exists)
            # then just append the coordinates and any other read in information
            else:
                missing_int_files.append(atom_name)

    # if there are missing atoms, then print these out
    if len(missing_int_files) > 0:

        if print_missing_data:
            print(
                f"Point {point.path} has missing .int files for atoms: {missing_int_files}."
            )

    return point_dict
