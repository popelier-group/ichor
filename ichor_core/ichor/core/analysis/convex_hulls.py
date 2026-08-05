import os, glob
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull


class ConvexHullAnalysis:
    """Class for performing convex hull analysis on molecular trajectories"""

    def __init__(self):
        pass

    def trajectory_from_path(self, xyzpath):
        """
            This function takes an XYZ file and reads the coordinates and atom names
            Inputs:
                xyzpath (string): path to an XYZ trajectory
        Outputs:
            traj_coords (numpy array): NxAx3 array where N is the number of frames, A is the number of atoms in the molecule
            atom_names (list): list of atom names i.e. C1, O2, H3...
        """
        separated_xyzs = []
        with open(xyzpath) as file:
            lines = [line.rstrip() for line in file]
            atomcount = int(lines[0])
            counter = atomcount + 2  # since xyz format has 2 lines at the top

            # split trajectory into frames
            for y in range(len(lines)):
                if (y + 1) % counter == 0:
                    separated_xyzs.append(lines[y - (counter - 1) : y + 1])

        traj_coords = []

        # split frames into coordinates
        for x in range(len(separated_xyzs)):
            traj_coords.append(
                np.array(
                    [row.split()[1:] for row in separated_xyzs[x][2:]], dtype="float"
                )
            )

        traj_coords = np.array(traj_coords)

        atoms = [
            row.split()[0] for row in separated_xyzs[0][2:]
        ]  # read atom names from first frame
        atom_names = [f"{atom}{i+1}" for i, atom in enumerate(atoms)]

        return traj_coords, atom_names

    def df_from_path(self, inputpath):
        """
        This function takes the path to an XYZ trajectory or a directory of XYZs
        and outputs a dataframe of convex hull data
        (number of points, area/volume sums/averages, atomic areas/volumes, percentage contributions to total area/volume)
        Inputs:
            inputpath (string): path to an XYZ file or directory of XYZ files
        Outputs:
         df (pandas dataframe) containing convex hull data
        """
        if os.path.isdir(inputpath):
            xyz_paths = glob.glob(f"{inputpath}/*.xyz")
        if os.path.isfile(inputpath):
            xyz_paths = [inputpath]

        column_volumes = []
        volume_sums = []
        volume_avgs = []
        point_counts = []
        atomic_areas = []
        area_avgs = []
        area_sums = []
        avg_densities = []

        atomic_volume_contributions_column = []
        atomic_area_contributions_column = []

        for i, path in enumerate(xyz_paths):

            # Reading xyz
            traj_coords, atom_names = self.trajectory_from_path(path)

            # Convex hull, atomic properties
            point_counts.append(int(len(traj_coords)))
            volumes = []
            areas = []
            for atomindex in range(len(atom_names)):  # loop over atoms
                selected_coords = [
                    i[atomindex] for i in traj_coords
                ]  # selecting one atom
                hull = ConvexHull(selected_coords)
                #         print(f"{atom_names[atomindex]}: {hull.volume}")
                volumes.append(hull.volume)
                #             print(hull.volume)
                areas.append(hull.area)
            atomic_areas.append(areas)
            area_sums.append(sum(areas))
            area_avgs.append(sum(areas) / len(areas))
            volume_sums.append(sum(volumes))
            volume_avgs.append(sum(volumes) / len(volumes))
            column_volumes.append(volumes)
            avg_densities.append(len(volumes) / sum(volumes))

            # Atomic % contribution to total volume, area
            atomic_volume_contributions = []
            atomic_area_contributions = []

            for atomindex in range(len(atom_names)):  # loop over atoms

                selected_coords = [
                    c[atomindex] for c in traj_coords
                ]  # selecting one atom
                hull = ConvexHull(selected_coords)
                #         print(f"{atom_names[atomindex]}: {hull.volume}")

                # Calculate percentage contributions from each atom
                atomic_volume_contributions.append(100 * hull.volume / volume_sums[i])
                atomic_area_contributions.append(100 * hull.area / area_sums[i])

            atomic_volume_contributions_column.append(atomic_volume_contributions)
            atomic_area_contributions_column.append(atomic_area_contributions)

        # data for each atom, i.e. Volumes and surface areas

        data = [
            volumes
            + atomic_areas[i]
            + atomic_volume_contributions_column[i]
            + atomic_area_contributions_column[i]
            for i, volumes in enumerate(column_volumes)
        ]

        column_labels = [os.path.basename(i)[:-4] for i in xyz_paths]

        # Ordering of index labels should match ordering of atomic data
        index_labels = (
            [i + " volume" for i in [atom_names][0]]
            + [i + " area" for i in [atom_names][0]]
            + [i + " % volume" for i in [atom_names][0]]
            + [i + " % area" for i in [atom_names][0]]
        )

        other_data = [
            avg_densities,
            volume_avgs,
            volume_sums,
            area_avgs,
            area_sums,
            point_counts,
        ]
        other_data_labels = [
            "Density",
            "Volume avg",
            "Volume sum",
            "Area avg",
            "Area sum",
            "Number of points",
        ]

        for i in other_data_labels:
            index_labels.insert(0, i)

        for i in range(len(data)):  # Loop over number of trajectories loaded
            for stat in other_data:
                data[i].insert(0, stat[i])

        data = np.array(data).T

        df = pd.DataFrame(data, index=index_labels, columns=column_labels)

        return df
