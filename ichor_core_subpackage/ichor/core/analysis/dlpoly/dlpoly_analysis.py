from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
from ichor.core.common.constants import ha_to_kj_mol
from ichor.core.common.io import get_files_of_type
from ichor.core.common.np import dict_of_list_to_dict_of_array
from ichor.core.files import WFN
from ichor.core.models import Models


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
    optimum_energy: float,
    dlpoly_directory: Path,
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
            wfn_files = get_files_of_type(WFN.get_filetype(), d)
            if len(wfn_files) > 0:
                data["gaussian"] += [read_wfn_energy(wfn_files[0])]
            else:
                data["gaussian"] += [np.NaN]

    data = dict_of_list_to_dict_of_array(data)

    if np.isnan(data["gaussian"]).all():
        del data["gaussian"]

    df = pd.DataFrame(data)
    df.sort_values("ntrain", inplace=True)

    if optimum_energy is not None:
        df["fflux_diff / Ha"] = np.abs(df["fflux"] - optimum_energy)
        df["fflux_diff / kJ/mol"] = df["fflux_diff / Ha"] * ha_to_kj_mol
        if "gaussian" in df.columns:
            df["gaussian_diff / Ha"] = np.abs(df["gaussian"] - optimum_energy)
            df["gaussian_diff / kJ/mol"] = df["gaussian_diff / Ha"] * ha_to_kj_mol

    df.to_excel(output, index=False)
