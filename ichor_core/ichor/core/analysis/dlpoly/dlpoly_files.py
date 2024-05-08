# from ichor.core.files.file import WriteFile
# from ichor.core.common.io import convert_to_path
# from typing import Union
# from pathlib import Path
# from ichor.core.atoms import Atoms
# from ichor.core.calculators.geometry_calculator import get_internal_feature_indices
# from ichor.core.constants import dlpoly_weights


# TODO: move these to menus
# def link_models(path: Path, models: Models):
#     model_dir = path / "model_krig"
#     mkdir(model_dir)
#     for model in models:
#         ln(model.path.absolute(), model_dir)

# def setup_dlpoly_directory(
#     path: Path, atoms: Atoms, models: Models, temperature: float = 0.0
# ):
#     mkdir(path)
#     write_control(path, temperature=temperature)
#     write_config(path, atoms)
#     write_field(path, atoms)
#     link_models(path, models)

# def get_dlpoly_directories(models: List[Models]) -> List[Path]:
#     dlpoly_directories = []
#     for model in models:
#         dlpoly_directories.append(
#             FILE_STRUCTURE["dlpoly"]
#             / f"{model.system}{str(model.ntrain).zfill(4)}"
#         )
#     return dlpoly_directories


# @convert_to_path
# def setup_dlpoly_directories(
#     atoms: Atoms, models: List[Models], temperature: float = 0.0
# ) -> List[Path]:
#     dlpoly_directories = get_dlpoly_directories(models)
#     for dlpoly_dir, model in zip(dlpoly_directories, models):
#         setup_dlpoly_directory(
#             dlpoly_dir, atoms, model, temperature=temperature
#         )
#     return dlpoly_directories
