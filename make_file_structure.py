import subprocess
from pathlib import Path

from ichor.core.common.io import remove
from ichor.hpc.global_variables import FILE_STRUCTURE

base_path = Path("test")
file_name = "file_structure.html"

for key, val in FILE_STRUCTURE.items():
    (base_path / val.path).mkdir(parents=True, exist_ok=True)

res = subprocess.run(
    ["tree", "-R", "-a", "-d", "./test", "-o", file_name, "-H", "./test"],
    capture_output=True,
)

with open(file_name, "r") as htmlfile:

    lines = htmlfile.readlines()

    for idx, line in enumerate(lines):

        if "<h1" in line:

            lines[idx] = line.replace("Directory Tree", "ichor directory tree")

        elif "<a" in line:
            for key, val in FILE_STRUCTURE.items():
                if ">" + str(val.name) + "<" in line:
                    to_add = '<a title="' + str(val.description) + '"'
                    lines[idx] = line.replace("<a", to_add)
                    break

with open(file_name, "w") as htmlfile:

    for line in lines:

        htmlfile.write(line)

remove(base_path)
