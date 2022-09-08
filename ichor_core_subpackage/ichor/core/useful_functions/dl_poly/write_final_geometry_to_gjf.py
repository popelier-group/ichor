from pathlib import Path

def write_final_geometry_to_gjf(
    dlpoly_directory: Path,
) -> Path:

    from ichor.core.files import GJF, DlpolyHistory

    for d in dlpoly_directory.iterdir():
        if d.is_dir() and (d / "HISTORY").exists():
            dlpoly_history = DlpolyHistory(d / "HISTORY")
            gjf = GJF(d / (d.name + GJF.filetype))
            gjf.atoms = dlpoly_history[-1]
            gjf.write()
            
    return gjf.path