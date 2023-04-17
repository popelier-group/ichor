from ichor.hpc.global_variables import FILE_STRUCTURE
from ichor.hpc.submission_script.script_names import ScriptNames

SCRIPT_NAMES = ScriptNames(
    {"pd_to_sqlite3": "pd_to_sqlite3.sh", "pd_to_csvs": "pd_to_csvs.sh"},
    parent=FILE_STRUCTURE["scripts"],
)
