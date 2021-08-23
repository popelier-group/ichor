from ichor.common import Daemon
import os
from ichor.common.io import get_files_of_type
from ichor.auto_run.per.per import auto_run_per_value


class PerAtomDaemon(Daemon):
    def __init__(self):
        from ichor.globals import GLOBALS
        cwd = os.getcwd()
        pidfile = GLOBALS.CWD / GLOBALS.FILE_STRUCTURE["atoms_pid"]
        stdout = GLOBALS.CWD / GLOBALS.FILE_STRUCTURE["atoms_stdout"]
        stderr = GLOBALS.CWD / GLOBALS.FILE_STRUCTURE["atoms_stderr"]
        super().__init__(pidfile, stdout=stdout, stderr=stderr)

    def run(self):
        auto_run_per_atom()
        self.stop()


def auto_run_per_atom() -> None:
    from ichor.globals import GLOBALS

    atoms = [atom.name for atom in GLOBALS.ATOMS]
    auto_run_per_value("OPTIMISE_ATOM", atoms, directory=GLOBALS.FILE_STRUCTURE["atoms"])



# @staticmethod
# def run():
#     original_atom = GLOBALS.OPTIMISE_ATOM
#
#     atom_directories = []
#     try:
#         gjf_file = FileTools.get_first_gjf(
#             GLOBALS.FILE_STRUCTURE["training_set"]
#         )
#         atoms = GJF(gjf_file, read=True).atoms.atoms
#     except:
#         xyz_files = FileTools.get_files_in(".", "*.xyz")
#         if len(xyz_files) == 0:
#             printq("Error: No xyz file or TRAINING_SET found")
#         elif len(xyz_files) > 1:
#             printq("Error: Too many xyz files found")
#         traj = Trajectory(xyz_files[0]).read(n=1)
#         atoms = traj[0].atoms
#     atoms_root = GLOBALS.FILE_STRUCTURE["atoms"]
#
#     print()
#     if not os.path.exists(atoms_root):
#         # make directory
#         print(f"Making {atoms_root}")
#         FileTools.mkdir(atoms_root, empty=False)
#         print()
#         # make property directories
#         print("Making Atom Directories")
#         with tqdm(total=len(atoms), unit=" dirs") as progressbar:
#             for atom_name in atoms:
#                 progressbar.set_description(atom_name)
#
#                 atom_directory = os.path.join(atoms_root, atom_name)
#                 FileTools.mkdir(atom_directory, empty=False)
#                 atom_directories += [(atom_name, atom_directory)]
#
#                 progressbar.update()
#         print()
#         if FileTools.dir_exists(GLOBALS.FILE_STRUCTURE["training_set"]):
#             # copy training set
#             print("Copying Training Set")
#             with tqdm(total=len(atoms), unit=" dirs") as progressbar:
#                 for _, atom_directory in atom_directories:
#                     progressbar.set_description(atom_directory)
#                     dst = os.path.join(
#                         atom_directory,
#                         GLOBALS.FILE_STRUCTURE["training_set"],
#                     )
#                     FileTools.copytree(
#                         GLOBALS.FILE_STRUCTURE["training_set"], dst
#                     )
#                     progressbar.update()
#             print()
#             # copy sample pool
#             print("Copying Sample Pool")
#             with tqdm(total=len(atoms), unit=" dirs") as progressbar:
#                 for _, atom_directory in atom_directories:
#                     progressbar.set_description(atom_directory)
#                     dst = os.path.join(
#                         atom_directory,
#                         GLOBALS.FILE_STRUCTURE["sample_pool"],
#                     )
#                     FileTools.copytree(
#                         GLOBALS.FILE_STRUCTURE["sample_pool"], dst
#                     )
#                     progressbar.update()
#         else:
#             xyz_files = FileTools.get_files_in(".", "*.xyz")
#             if len(xyz_files) == 0:
#                 printq("Error: No xyz file or TRAINING_SET found")
#             elif len(xyz_files) > 1:
#                 printq("Error: Too many xyz files found")
#             print(f"Copying XYZ File: {xyz_files[0]}")
#             with tqdm(total=len(atoms), unit=" xyz") as progressbar:
#                 for _, atom_directory in atom_directories:
#                     progressbar.set_description(atom_directory)
#                     dst = os.path.join(atom_directory, xyz_files[0])
#                     FileTools.copy_file(xyz_files[0], dst)
#                     progressbar.update()
#         print()
#
#     else:
#         for atom_name in atoms:
#             atom_directory = os.path.join(atoms_root, atom_name)
#             atom_directories += [(atom_name, atom_directory)]
#     # copy ICHOR.py
#     print("Copying ICHOR")
#     with tqdm(total=len(atoms), unit=" files") as progressbar:
#         for _, atom_directory in atom_directories:
#             progressbar.set_description(atom_directory)
#             FileTools.copy_file(os.path.realpath(__file__), atom_directory)
#             progressbar.update()
#     print()
#     # copy config.properties
#     print("Copying Config File")
#     with tqdm(total=len(atoms), unit=" files") as progressbar:
#         for atom_name, atom_directory in atom_directories:
#             progressbar.set_description(atom_directory)
#             GLOBALS.OPTIMISE_ATOM = atom_name
#             with FileTools.pushd(atom_directory):
#                 GLOBALS.save_to_config()
#             progressbar.update()
#     print()
#     # copy programs
#     print("Copying Programs")
#     with tqdm(total=len(atoms), unit=" files") as progressbar:
#         for _, atom_directory in atom_directories:
#             progressbar.set_description(atom_directory)
#             dst = os.path.join(
#                 atom_directory, GLOBALS.FILE_STRUCTURE["programs"]
#             )
#             FileTools.copytree(GLOBALS.FILE_STRUCTURE["programs"], dst)
#             progressbar.update()
#     print()
#     # run adaptive sampling
#     print("Submitting Adaptive Sampling Runs")
#     importlib.invalidate_caches()
#     for atom_name, atom_directory in atom_directories:
#         with FileTools.pushd(atom_directory):
#             spec = importlib.util.spec_from_file_location("*", __file__)
#             ichor = importlib.util.module_from_spec(spec)
#             try:
#                 spec.loader.exec_module(ichor)
#             except:
#                 print(
#                     f"Error submitting adaptive sampling for: {atom_name}"
#                 )
#             ichor.AutoTools.run_from_extern()
#
#     GLOBALS.OPTIMISE_ATOM = original_atom
#
# @staticmethod
# def collate_log():
#     FileTools.mkdir(GLOBALS.FILE_STRUCTURE["log"], empty=False)
#     for atoms_dir in FileTools.get_files_in(
#         GLOBALS.FILE_STRUCTURE["atoms"], "*/"
#     ):
#         log_dir = os.path.join(atoms_dir, GLOBALS.FILE_STRUCTURE["log"])
#         if os.path.exists(log_dir):
#             # for model_dir in FileTools.get_files_in(log_dir, f"{str(GLOBALS.SYSTEM_NAME)}*/"):
#             FileTools.copymodels(log_dir, GLOBALS.FILE_STRUCTURE["log"])
