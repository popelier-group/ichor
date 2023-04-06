from pathlib import Path


def write_final_geometry_to_gjf(dlpoly_directory: Path, **kwargs) -> Path:

    from ichor.core.files import DlpolyHistory, GJF

    for f in dlpoly_directory.iterdir():
        if f.name == "HISTORY":
            dlpoly_history = DlpolyHistory(f)
            gjf = GJF(dlpoly_directory / (f.name + GJF.filetype), **kwargs)
            gjf.atoms = dlpoly_history[-1]
            gjf.write()

    return gjf.path.absolute()
