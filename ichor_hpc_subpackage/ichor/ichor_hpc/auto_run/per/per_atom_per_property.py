from pathlib import Path

from ichor.auto_run.per.per import check_auto_run_per_counter
from ichor.auto_run.per.per_atom import PerAtomDaemon, auto_run_per_atom
from ichor.auto_run.per.per_property import auto_run_per_property
from ichor.ichor_hpc import FILE_STRUCTURE
from ichor.ichor_hpc import GLOBALS
from ichor.main.make_models import MODEL_TYPES


class PerAtomPerPropertyDaemon(PerAtomDaemon):
    def run(self):
        auto_run_per_atom_per_property()
        self.stop()


def run_per_atom_per_property_daemon():
    per_atom_per_property_values = []
    for atom in GLOBALS.ATOMS:
        for prop in MODEL_TYPES():
            per_atom_per_property_values.append(
                str(Path(atom.name) / FILE_STRUCTURE["properties"] / prop)
            )
    check_auto_run_per_counter(
        FILE_STRUCTURE["atoms"], per_atom_per_property_values
    )
    PerAtomPerPropertyDaemon().start()


def auto_run_per_atom_per_property() -> None:
    auto_run_per_atom(run_func=auto_run_per_property)
