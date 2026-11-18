from math import isfinite
from pathlib import Path
from shutil import copyfileobj, copymode
from tempfile import NamedTemporaryFile
from typing import Dict, Union

from ichor.core.atoms import Atom, Atoms
from ichor.core.common.constants import type2nuclear_charge
from ichor.core.common.units import AtomicDistance
from ichor.core.files.file import FileContents, ReadFile
from ichor.core.files.file_data import HasAtoms, HasData

nuclear_charge_to_type = {v: k for k, v in type2nuclear_charge.items()}


class MolecularOrbital:
    def __init__(
        self,
        index: int,
        eigen_value: float,
        occupation_number: float,
        energy: float,
        primitives: list,
    ):
        self.index = index
        self.eigen_value = eigen_value
        self.occupation_number = occupation_number
        self.energy = energy
        self.primitives = primitives


class WFX(HasAtoms, HasData, ReadFile):
    """Read geometry in Bohr and wavefunction metadata from an AIM WFX file."""

    _filetype = ".wfx"
    _energy = "energy = t + vne + vee + vnn"
    _virial = "virial ratio (-v/t)"
    _metadata = {
        "title", "model", "number of nuclei", "number of primitives",
        "number of occupied molecular orbitals", "atomic numbers",
        "nuclear cartesian coordinates", _energy, _virial,
    }

    def __init__(self, path: Union[Path, str], method: str = None):
        super().__init__(path)
        self.method = method or FileContents
        self.atoms = FileContents
        self.title = FileContents
        self.n_orbitals = FileContents
        self.n_primitives = FileContents
        self.n_nuclei = FileContents
        self.total_energy = FileContents
        self.virial_ratio = FileContents

    def _read_metadata(self):
        # WFX tags can contain spaces and are not XML element names.
        sections = {}
        stack = []
        with self.path.open(encoding="utf-8", errors="surrogateescape") as stream:
            for line in stream:
                line = line.strip()
                if line.startswith("</") and line.endswith(">"):
                    if not stack or stack.pop() != line[2:-1].casefold():
                        raise ValueError(f"Mismatched WFX section in {self.path}")
                elif line.startswith("<") and line.endswith(">"):
                    tag = line[1:-1].casefold()
                    stack.append(tag)
                    if len(stack) == 1 and tag in self._metadata:
                        sections[tag] = []
                elif len(stack) == 1 and stack[0] in sections:
                    if line:
                        sections[stack[0]].append(line)
        if stack:
            raise ValueError(f"Unclosed WFX section in {self.path}: {stack[-1]}")
        return {tag: " ".join(lines) for tag, lines in sections.items()}

    @staticmethod
    def _float(value):
        number = float(value.replace("D", "E").replace("d", "e"))
        if not isfinite(number):
            raise ValueError(f"Invalid WFX number: {value}")
        return number

    def _read_file(self):
        sections = self._read_metadata()
        try:
            n_nuclei = int(sections["number of nuclei"])
            n_primitives = int(sections["number of primitives"])
            n_orbitals = int(sections["number of occupied molecular orbitals"])
            atomic_numbers = sections["atomic numbers"].split()
            coordinates = sections["nuclear cartesian coordinates"].split()
            if (
                min(n_nuclei, n_primitives, n_orbitals) < 1
                or len(atomic_numbers) != n_nuclei
                or len(coordinates) != 3 * n_nuclei
            ):
                raise ValueError("Nuclear counts and coordinates disagree")
            atoms = Atoms()
            for index, atomic_number in enumerate(atomic_numbers):
                xyz = map(self._float, coordinates[3 * index : 3 * index + 3])
                atoms.append(
                    Atom(
                        nuclear_charge_to_type[int(atomic_number)],
                        *xyz,
                        units=AtomicDistance.Bohr,
                    )
                )
            total_energy = self._float(sections[self._energy])
            virial_ratio = self._float(sections[self._virial])
        except (KeyError, ValueError) as exc:
            raise ValueError(f"Invalid WFX metadata in {self.path}: {exc}") from exc

        self.n_nuclei = n_nuclei
        self.n_primitives = n_primitives
        self.n_orbitals = n_orbitals
        self.atoms = atoms
        self.total_energy = total_energy
        self.virial_ratio = virial_ratio
        self.title = sections.get("title", "")
        self.method = self.method or sections.get("model") or None

    @property
    def raw_data(self) -> Dict[str, float]:
        return {"energy": self.total_energy, "virial_ratio": self.virial_ratio}

    @property
    def properties(self) -> Dict[str, float]:
        return self.raw_data

    def ensure_model(self, method: str):
        """Add a missing AIMAll model while preserving all other WFX sections."""
        self.read()
        if self.method:
            return
        if not method or not method.isascii() or any(c in method for c in "<>\r\n"):
            raise ValueError("Expected a WFX model on one line")

        temporary_path = None
        try:
            with self.path.open("rb") as source, NamedTemporaryFile(
                dir=self.path.parent, delete=False
            ) as target:
                temporary_path = Path(target.name)
                target.write(f"<Model>\n{method}\n</Model>\n".encode("ascii"))
                copyfileobj(source, target)
            copymode(self.path, temporary_path)
            temporary_path.replace(self.path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        self.method = method
