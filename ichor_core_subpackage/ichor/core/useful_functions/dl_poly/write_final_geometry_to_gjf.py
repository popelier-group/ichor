from pathlib import Path

def write_final_geometry_to_gjf(dlpoly_directory: Path,) -> Path:

    from ichor.core.files import GJF, DlpolyHistory

    for f in dlpoly_directory.iterdir():
        if f.name == "HISTORY":
            dlpoly_history = DlpolyHistory(f)
            gjf = GJF(dlpoly_directory / (f.name + GJF.filetype))
            gjf.atoms = dlpoly_history[-1]
            gjf.write()
            
    return gjf.path.absolute()