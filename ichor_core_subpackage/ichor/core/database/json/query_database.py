import json
from pathlib import Path

import pandas as pd
from ichor.core.common.sorting import ignore_alpha
from natsort import natsorted

# these are taken from the sqlite version
# write in the same way so we can use the same function to process data
dataframe_cols = [
    "id",
    "date_added",
    "name",
    "wfn_energy",
    "x",
    "y",
    "z",
    "force_x",
    "force_y",
    "force_z",
    "iqa",
    "integration_error",
    "q00",
    "q10",
    "q11c",
    "q11s",
    "q20",
    "q21c",
    "q21s",
    "q22c",
    "q22s",
    "q30",
    "q31c",
    "q31s",
    "q32c",
    "q32s",
    "q33c",
    "q33s",
    "q40",
    "q41c",
    "q41s",
    "q42c",
    "q42s",
    "q43c",
    "q43s",
    "q44c",
    "q44s",
    "q50",
    "q51c",
    "q51s",
    "q52c",
    "q52s",
    "q53c",
    "q53s",
    "q54c",
    "q54s",
    "q55c",
    "q55s",
    "atom_name",
]


def get_json_db_info(db_path):
    """Gets important information from json database (a directory containing
    multiple json files) and returns point ids, atom names, and full
    pandas dataframe, which can be processed into atomic csvs

    :param db_path: path to directory containing json files storing data
    """

    id_counter = 1
    all_dfs = []

    for d in natsorted(Path(db_path).iterdir(), key=ignore_alpha):

        with open(d, "r") as f:

            json_data = json.load(f)

        for point in json_data:

            # store info for all atoms
            data_for_all_atoms_in_point = []

            point_name = point["name"]
            date_added = point["date_added"]
            wfn_energy = point["wfn_energy"]

            atomic_data = point.get("atomic_data")

            if atomic_data:
                for atom_name, atom_data_dict in atomic_data.items():

                    # this is data that is going to be the same for all atoms
                    # since they come from the same point
                    global_data_for_one_atom = []
                    global_data_for_one_atom.extend(
                        [id_counter, date_added, point_name, wfn_energy]
                    )

                    atomic_data_for_one_atom = []
                    atom_coords = atom_data_dict["coordinates"]
                    global_forces = atom_data_dict["global_forces"]
                    iqa = atom_data_dict["iqa"]
                    integration_error = atom_data_dict["integration_error"]
                    global_spherical_multipoles_dict = atom_data_dict[
                        "global_spherical_multipole_moments"
                    ]

                    atomic_data_for_one_atom.extend(atom_coords)
                    atomic_data_for_one_atom.extend(global_forces)
                    atomic_data_for_one_atom.append(iqa)
                    atomic_data_for_one_atom.append(integration_error)
                    atomic_data_for_one_atom.extend(
                        list(global_spherical_multipoles_dict.values())
                    )
                    atomic_data_for_one_atom.append(atom_name)

                    global_data_for_one_atom.extend(atomic_data_for_one_atom)
                    data_for_all_atoms_in_point.append(global_data_for_one_atom)

                id_counter += 1

            inner_df = pd.DataFrame(data_for_all_atoms_in_point, columns=dataframe_cols)
            all_dfs.append(inner_df)

    total_df = pd.concat(all_dfs)
    # reset the index column so that it starts at 1
    # drop=True to remove the old index col
    total_df = total_df.reset_index(drop=True)

    return list(set(total_df["id"])), list(set(total_df["atom_name"])), total_df
