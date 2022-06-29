import inspect
from contextlib import suppress
from typing import Optional

from ichor.hpc.globals import Globals


def get_note(variable_name: str, source_code: str) -> Optional[str]:
    for line in source_code.split("\n"):
        if "def __init__" in line:
            break
        if f"{variable_name}:" in line and "#" in line:
            return line.split("#")[-1]


if __name__ == "__main__":
    with open("globals.md", "w") as f:
        globals = Globals()
        globals_source = inspect.getsource(Globals)
        f.write("| Name | Type | Default Value | Notes |\n")
        f.write("| --- | --- | --- | --- |\n")
        for global_variable in globals._global_variables:
            with suppress(KeyError):
                if global_variable not in globals._protected:
                    ty = None
                    global_type = globals.__annotations__[global_variable]
                    try:
                        ty = global_type.__name__
                    except AttributeError:
                        if hasattr(global_type, "__bases__"):
                            ty = global_type.__bases__.replace("typing.", "")
                        else:
                            ty = str(global_type)
                    note = get_note(global_variable, globals_source)
                    note = note.strip() if note is not None else ""
                    f.write(
                        f"| {global_variable} | {global_type} | {globals._defaults[global_variable]} | {note} |\n"
                    )
