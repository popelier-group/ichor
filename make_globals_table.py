import re
import ichor.globals.globals as globals
from pathlib import Path

docstr = globals.__doc__.split("\n")

new_docstring = ""

for line in docstr:

    # all lines that are not part of the md table
    if not line.startswith("|"):
        line.strip()
        line += "\n"
        new_docstring += line

    else:
        parts = line.split("|")
        parts = [part for part in parts if part != ""]
        new_line = "|"

        for part in parts:

            part = part.strip()
            new_line += part
            new_line += "|"
            
        new_line += "\n"
        new_docstring += new_line

dest = Path("examples/globals_table.md")

with open(str(dest), "w+") as f:

    f.write(new_docstring)