from pathlib import Path

from ichor.core.files import AIM, INT
from ichor.core.files.file import FileContents


def aimall_completed(wfn: Path) -> bool:
    """This function is used when checking if AIMALL ran successfully.
    It checks if AIM file exists, and checks if the INT files
    exist. Note that it assumes that IQA energy is also calculated
    The .aim file as well as if the .int files contain the required information."""

    aim_file = wfn.with_suffix(AIM.filetype)
    if not aim_file.exists():
        return False
    aim = AIM(aim_file)
    for atom, aimdata in aim.items():
        if not aimdata.outfile.exists():
            print(f"AIMAll for {wfn} failed to run for atom '{atom}'")
            return False
        else:
            int_file = INT(aimdata.outfile)
            try:
                assert int_file.integration_error is not FileContents
                assert int_file.q44s is not FileContents
                assert int_file.iqa is not FileContents
            except AttributeError:
                print(
                    f"AIMAll for '{wfn}' failed to run producing invalid int file '{int_file.path}'"
                )
                return False
    return True
