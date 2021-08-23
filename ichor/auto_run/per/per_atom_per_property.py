from ichor.auto_run.per.per import auto_run_per_value
from ichor.auto_run.per.per_atom import PerAtomDaemon, auto_run_per_atom
from ichor.auto_run.per.per_property import auto_run_per_property
from ichor.common import Daemon


class PerAtomPerPropertyDaemon(PerAtomDaemon):
    def run(self):
        auto_run_per_atom_per_property()
        self.stop()


def auto_run_per_atom_per_property() -> None:
    auto_run_per_atom(run_func=auto_run_per_property)
