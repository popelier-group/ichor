from pathlib import Path
from ichor.file_structure import FILE_STRUCTURE
from ichor.common.types import FileType
from ichor.files.file import File 
from ichor.common.io import mkdir

for ref_name, node in FILE_STRUCTURE.items():

    if node.type_ is FileType.Directory:
        mkdir(Path("ICHOR_FILE_STRUCTURE") / node.path)

for ref_name, node in FILE_STRUCTURE.items():

    if node.type_ is FileType.File:
        (Path("ICHOR_FILE_STRUCTURE") / node.path).touch()