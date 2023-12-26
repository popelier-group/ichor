from pathlib import Path
from typing import List

from ichor.core.atoms import ALF
from ichor.core.sql.query_database import get_alf_from_first_db_geometry
from ichor.hpc.global_variables import SCRIPT_NAMES
from ichor.hpc.submission_commands.free_flow_python_command import FreeFlowPythonCommand
from ichor.hpc.submission_script import SubmissionScript
from ichor.hpc.useful_functions.compile_strings_to_python_code import (
    compile_strings_to_python_code,
)
from ichor.hpc.useful_functions.submit_free_flow_python_on_compute import (
    submit_free_flow_python_command_on_compute,
)


def submit_make_csvs_from_database(
    db_path: Path,
    ncores: int,
    alf: List[ALF] = None,
    float_difference_iqa_wfn: float = 4.184,
    float_integration_error: float = 1e-3,
    rotate_multipole_moments: bool = True,
    calculate_feature_forces: bool = False,
):
    """Submits making of csv files from a databse to compute node.
    Note that the csv making code is parallelized per atom, meaning that
    each atomic csv is made using 1 core. Using the same number of cores
    as the number of atoms in the system is the optimal choice.

    :param db_path: pathlib.Path object that holds path to database
    :param ncores: Number of cores to run job with
    :param float_difference_iqa_wfn: Absolute tolerance for difference of energy
        between WFN and sum of IQA energies.
    :param float_integration_error: Absolute tolerance for integration error.
    :param alf: A list of ALF for the whole system. If not given,
        it will be calculated automatically.
    :param rotate_multipole_moments: Whether or not to rotate multipole
        moments, defaults to True
    :param calculate_feature_forces: Whether or not to calculate ALF forces, defaults to False
    """

    # if no alf is given, then automatically calculate it
    if not alf:
        alf = get_alf_from_first_db_geometry(db_path)

    text_list = []
    # make the python command that will be written in the submit script
    # it will get executed as `python -c python_code_to_execute...`
    text_list.append(
        "from ichor.core.sql.query_database import write_processed_data_for_atoms_parallel"
    )
    text_list.append("from pathlib import Path")
    text_list.append("from ichor.core.atoms import ALF")
    text_list.append(f"db_path = Path('{db_path.absolute()}')")
    text_list.append(f"alf = {alf}")
    str_part1 = f"write_processed_data_for_atoms_parallel(db_path, alf, {ncores},"
    str_part2 = f" max_diff_iqa_wfn={float_difference_iqa_wfn},"
    str_part3 = f" max_integration_error={float_integration_error},"
    str_part4 = f" calc_multipoles={rotate_multipole_moments}, calc_forces={calculate_feature_forces})"
    text_list.append(str_part1 + str_part2 + str_part3 + str_part4)

    final_cmd = compile_strings_to_python_code(text_list)
    py_cmd = FreeFlowPythonCommand(final_cmd)
    with SubmissionScript(
        SCRIPT_NAMES["calculate_features"], ncores=ncores
    ) as submission_script:
        submission_script.add_command(py_cmd)
    submission_script.submit()

    return submit_free_flow_python_command_on_compute(
        text_list=text_list,
        script_name=SCRIPT_NAMES["calculate_features"],
        ncores=ncores,
    )
