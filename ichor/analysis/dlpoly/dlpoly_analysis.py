from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ichor.analysis.dlpoly.dlpoly_files import (
    DlpolyHistory,
    get_dlpoly_directories,
    setup_dlpoly_directories,
)
from ichor.analysis.dlpoly.dlpoly_submit import (
    submit_dlpoly_gjfs,
    submit_dlpoly_jobs,
)
from ichor.analysis.get_atoms import get_atoms_from_path
from ichor.analysis.get_models import get_models_from_path
from ichor.analysis.opt import find_opt
from ichor.batch_system import JobID
from ichor.common.io import get_files_of_type
from ichor.common.np import dict_of_list_to_dict_of_array
from ichor.constants import ha_to_kj_mol
from ichor.file_structure import FILE_STRUCTURE
from ichor.files import GJF, WFN
from ichor.models import Models


def run_dlpoly(
    dlpoly_input: Path,
    model_location: Path,
    temperature: float = 0.0,
    hold=Optional[JobID],
) -> JobID:
    dlpoly_input_atoms = get_atoms_from_path(dlpoly_input)
    dlpoly_input_models = get_models_from_path(model_location)
    dlpoly_directories = setup_dlpoly_directories(
        dlpoly_input_atoms, dlpoly_input_models, temperature=temperature
    )
    return submit_dlpoly_jobs(dlpoly_directories, hold=hold)


def run_dlpoly_geometry_optimisations(
    dlpoly_input: Path, model_location: Path, hold=Optional[JobID]
) -> JobID:
    return run_dlpoly(dlpoly_input, model_location, temperature=0.0)


def write_final_geometry_to_gjf(
    dlpoly_directory: Path = FILE_STRUCTURE["dlpoly"],
) -> List[Path]:
    gjfs = []
    for d in dlpoly_directory.iterdir():
        if d.is_dir() and (d / "HISTORY").exists():
            dlpoly_history = DlpolyHistory(d / "HISTORY")
            gjf = GJF(d / (d.name + GJF.filetype))
            gjf.atoms = dlpoly_history[-1]
            gjf.write()
            gjfs += [gjf.path]
    return gjfs


def submit_final_geometry_to_gaussian(
    dlpoly_directory: Path = FILE_STRUCTURE["dlpoly"],
    hold: Optional[JobID] = None,
) -> JobID:
    gjfs = write_final_geometry_to_gjf(dlpoly_directory)
    return submit_dlpoly_gjfs(gjfs, hold=hold)


def read_fflux(fflux_file: Path) -> Dict[str, np.ndarray]:
    data = {
        "timestep": [],
        "e_iqa": [],
        "e_vdw": [],
        "e_coul": [],
    }
    with open(fflux_file, "r") as f:
        _ = next(f)  # title
        _ = next(f)  # comment line
        for line in f:
            record = line.split()
            # record = timestep e_iqa e_vdw e_coul
            data["timestep"] += [int(record[0])]
            data["e_iqa"] += [float(record[1])]
            data["e_vdw"] += [float(record[2])]
            data["e_coul"] += [float(record[3])]

    return dict_of_list_to_dict_of_array(data)


def read_wfn_energy(wfn_file: Path) -> float:
    return WFN(wfn_file).energy


def get_dlpoly_energies(
    dlpoly_directory: Path = FILE_STRUCTURE["dlpoly"],
    output: Path = Path("dlpoly-energies.xlsx"),
):
    data = {
        "ntrain": [],
        "fflux": [],
        "gaussian": [],
    }
    for d in dlpoly_directory.iterdir():
        if d.is_dir() and (d / "FFLUX").exists():
            data["ntrain"] += [Models(d / "model_krig").ntrain]
            data["fflux"] += [read_fflux(d / "FFLUX")["e_iqa"][-1]]
            wfn_files = get_files_of_type(WFN.filetype, d)
            if len(wfn_files) > 0:
                data["gaussian"] += [read_wfn_energy(wfn_files[0])]
            else:
                data["gaussian"] += [np.NaN]

    data = dict_of_list_to_dict_of_array(data)

    if np.isnan(data["gaussian"]).all():
        del data["gaussian"]

    df = pd.DataFrame(data)
    df.sort_values("ntrain", inplace=True)

    optimum_energy = find_opt()
    if optimum_energy is not None:
        df["fflux_diff / Ha"] = np.abs(df["fflux"] - optimum_energy)
        df["fflux_diff / kJ/mol"] = df["fflux_diff / Ha"] * ha_to_kj_mol
        if "gaussian" in df.columns:
            df["gaussian_diff / Ha"] = np.abs(df["gaussian"] - optimum_energy)
            df["gaussian_diff / kJ/mol"] = (
                df["gaussian_diff / Ha"] * ha_to_kj_mol
            )

    df.to_excel(output, index=False)
