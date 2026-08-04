import numpy as np

class Sample:
    """
    Handles the subsampling of atomic trajectory data from a HISTORY file
    and writes each selected timestep to an XYZ file immediately (streaming)
    to avoid building a large in-memory trajectory.

    Parameters:
        histfile (str): Path to the HISTORY file containing trajectory data.
        outfile (str): Output path for the subsampled trajectory in XYZ format.
    """

    def __init__(self, histfile, outfile):
        self.histfile = histfile
        self.outfile = outfile

    def Sub_sample(self, stride, min_step=0, max_step=1e50, exact_step=None, simulation_max_step=False):
        """
        Extracts and writes selected snapshots from the HISTORY file.

        Parameters:
            stride (int): Sampling frequency in terms of timesteps.
            min_step (int): Minimum timestep to include in sampling.
            max_step (int): Maximum timestep to include in sampling.
            exact_step (int or None): Extract only this specific timestep.
            simulation_max_step (boolean): Extract only the last timestep.
        """
        self.atom_names = []
        timestep_count = 0
        timestep_flag = False

        # --- First pass: discover atom names from the first timestep block ---
        with open(self.histfile, "r") as f:
            for line in f:
                if "timestep" in line:
                    # We are now within a timestep block
                    timestep_count += 1
                    timestep_flag = True
                    if timestep_count == 2:
                        break

                if timestep_count == 1 and timestep_flag:
                    split_line = line.split()

                    if len(split_line) in [4, 5]:
                        self.atom_names.append(split_line[0])
                        atom_index = int(split_line[1])

                        # Detect corruption: if the atom index doesn't match the number of names collected
                        if atom_index != len(self.atom_names):
                            # Reset and start over if corruption is detected
                            timestep_flag = False
                            self.atom_names = []
                            timestep_count = 0
                            # Start over with the next occurrence of 'timestep'
                            continue

            # If user asked for the simulation's last step, find it by scanning from the end
            if simulation_max_step is True:
                with open(self.histfile, "r") as ff:
                    lines = ff.readlines()
                    for line in reversed(lines):
                        if "timestep" in line:
                            last_step = int(line.split()[1])
                            break

        # --- Second pass: stream snapshots and write each selected one immediately ---
        with open(self.histfile, "r") as f, open(self.outfile, "w") as out_f:
            atoms_tmp = []
            time_step_flag = False
            capture_next_line = False
            atom_num = 0
            time_tmp = None

            for line in f:
                if "timestep" in line:
                    current_step = int(line.split()[1])
                    # first check if we are after minimum requested step
                    if current_step < min_step:
                        continue
                    # then check if we are before maximum requested step
                    if current_step > max_step:
                        break
                    # decide whether we should capture this timestep
                    if simulation_max_step and current_step == last_step:
                        time_tmp = current_step
                        time_step_flag = True

                    elif simulation_max_step is not True and exact_step is not None and current_step == exact_step:
                        time_tmp = current_step
                        time_step_flag = True

                    elif simulation_max_step is not True and exact_step is None and ((current_step % stride) == 0):
                        time_tmp = current_step
                        time_step_flag = True

                    else:
                        # not interested in this timestep
                        time_step_flag = False

                elif time_step_flag and atom_num < len(self.atom_names):
                    parts = line.split()
                    if len(parts) in [4, 5]:
                        # the next line contains coordinates
                        capture_next_line = True
                    elif capture_next_line:
                        atoms_tmp.append(parts)
                        capture_next_line = False
                        atom_num += 1

                        # write the data
                        if atom_num == len(self.atom_names):
                            # write snapshot to file in XYZ-like format
                            out_f.write(f"{len(self.atom_names)}\n")
                            out_f.write(f"timestep: {time_tmp}\n")
                            for j, xyz in enumerate(atoms_tmp):
                                out_f.write(f"{self.atom_names[j]} {' '.join(xyz)}\n")
                            out_f.flush()

                            # reset for next snapshot
                            atoms_tmp = []
                            time_step_flag = False
                            atom_num = 0
                            time_tmp = None



s = Sample("HISTORY", "sub_history.xyz")
s.Sub_sample(stride=10,simulation_max_step=False)

