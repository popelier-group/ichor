# functions to check files / directories are present
from ichor.core.files import PointDirectory


def check_gaussian_and_aimall(pd_instance: PointDirectory):
    """A basic check function that checks if files Gaussian and AIMAll related files are
    missing. The outputs are printed to standard output or if submitted to a compute
    node, it is printed to the file containing standard output during the job.

    :param pd_instance: PointDirectory instance to check
    """

    abs_path = str(pd_instance.path.absolute())
    natoms = len(pd_instance.xyz.atoms)

    if not pd_instance.gjf:
        print(f"{abs_path}: GJF file is missing.")
    if not pd_instance.gaussian_output:
        print(f"{abs_path}: GaussianOutput file is missing.")

    if not pd_instance.ints:
        print(f"{abs_path}: IntDirectory directory is missing.")

    else:
        nints = len(pd_instance.ints.ints)
        if nints != natoms:
            print(
                f"{abs_path}: There are {nints} INT files found, but there are {natoms} atoms."
            )

    for f in pd_instance.iterdir():
        if f.suffix == ".sh":
            print(
                f"{abs_path}: There is a .sh file found, likely that AIMAll has crashed."
            )
