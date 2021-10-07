from ichor.files.file import File
from ichor.files.geometry import GeometryFile
from pathlib import Path
from enum import Enum
from ichor.atoms import Atom, Atoms
from ichor.units import AtomicDistance
from typing import Optional, List, Tuple
from ichor.common.functools import classproperty
from ichor.globals import GLOBALS
from ichor.common.os import current_user
import datetime
from ichor.analysis.geometry import bonds


class MoleculeType(Enum):
    Small = "SMALL"
    BioPolymer = "BIOPOLYMER"
    Protein = "PROTEIN"
    NucleicAcid = "NUCLEIC_ACID"
    Saccharide = "SACCHARIDE"


class ChargeType(Enum):
    NoCharges = "NO_CHARGES"
    DelRe = "DEL_RE"
    Gasteiger = "GASTEIGER"
    GastHuck = "GAST_HUCK"
    Huckel = "HUCKEL"
    Pullman = "PULLMAN"
    Gaussian = "GAUSS80_CHARGES"
    Ampac = "AMPAC_CHARGES"
    Mulliken = "MULLIKEN_CHARGES"
    Dict = "DICT_CHARGES"
    MMFF94 = "MMFF94_CHARGES"
    User = "USER_CHARGES"


class SybylStatus(Enum):
    System = "system"
    InvalidCharges = "invalid_charges"
    Analyzed = "analyzed"
    Substituted = "substituted"
    Altered = "altered"
    RefAngle = "ref_angle"
    NONE = "****"


class AtomType(Enum):
    Al = "Al"        # (aluminum)
    Br = "Br"        # (bromine)
    C1 = "C.1"       # (sp carbon)
    C2 = "C.2"       # (sp2 carbon)
    C3 = "C.3"       # (sp3 carbon)
    CAr = "C.ar"     # (aromatic carbon)
    CCat = "C.cat"   # (carbon)
    Ca = "Ca"        # (calcium)
    Cl = "Cl"        # (aromatic carbon)
    Dummy = "Du"     # (dummy atom-used as a placeholder)
    F = "F"          # (fluorine)
    H = "H"          # (hydrogen)
    HSPC = "H.spc"   # (hydrogen-water spc model)
    HT3P = "H.t3p"   # (hydrogen-water tip3p model)
    I = "I"          # (iodine)
    K = "K"          # (potassium)
    Li = "Li"        # (lithium)
    LonePair = "LP"  # (lone pair electrons)
    N1 = "N.1"       # (sp nitrogen)
    N2 = "N.2"       # (sp2 nitrogen)
    N3 = "N.3"       # (sp3 nitrogen)
    N4 = "N.4"       # (quaternary nitrogen)
    NAm = "N.am"     # (amide nitrogen)
    NAr = "N.ar"     # (aromatic nitrogen)
    NP13 = "N.p13"   # (trigonal nitrogen)
    Na = "Na"        # (sodium)
    O2 = "O.2"       # (sp2 oxygen)
    O3 = "O.3"       # (sp3 oxygen)
    OCO2 = "O.co2"   # (carboxy oxygen)
    OSPC = "O.spc"   # (oxygen-water spc model)
    OT3P = "O.t3p"   # (oxygen-water tip3p model)
    P3 = "P.3"       # (sp3 phosphorous)
    S2 = "S.2"       # (sp2 sulfur)
    S3 = "S.3"       # (sp3 sulfur)
    SO = "S.o"       # (sulfoxide sulfur)
    SO2 = "S.o2"     # (sulfone sulfur)
    Si = "Si"        # (silicon)
    CoOH = "Co.oh"   # (cobalt)
    RuOH = "Ru.oh"   # (Ruthenium)


class BondType(Enum):
    Single = "1"
    Double = "2"
    Triple = "3"
    Aromatic = "ar"
    Amide = "am"
    Unspecified = "un"


simple_types = {
    "D": AtomType.H,
    "P": AtomType.P3,
    "Co": AtomType.CoOH,
    "Ru": AtomType.RuOH,
}


def get_bond_type(atom1: Atom, atom2: Atom) -> BondType:
    pass

def acyclic_bond(atom1: Atom, atom2: Atom) -> bool:
    return True

def other_atom(atom: Atom, atom1: Atom, atom2: Atom) -> Atom:
    if atom.name == atom1.name:
        return atom2
    elif atom.name == atom2.name:
        return atom1
    else:
        raise ValueError(f"{atom} not in bond Bond({atom1}, {atom2})")

def other_atom_bonds(atom, atom1, atom2, parent) -> List[Tuple[int, int]]:
    return get_atom_bonds(other_atom(atom, atom1, atom2), parent)

def get_atom_bonds(atom, parent) -> List[Tuple[int, int]]:
    return [bond for bond in bonds(parent) if atom.index in bond]

def other_atoms(atom, parent) -> List[Atom]:
    return [other_atom(atom, parent[i-1], parent[j-1]) for i, j in get_atom_bonds(atom, parent)]

def nonmet(atom, parent):
    return sum(at in non_metal_atoms for at in [atom.type for atom in other_atoms(atom, parent)])


def bonds_of_type(atom, parent, bond_type):
    return [b for b in get_atom_bonds(atom, parent) if get_bond_type(parent[b[0]-1], parent[b[1]-1])]

def n_bonds_of_type(atom, parent, bond_type):
    return len(bonds_of_type(atom, parent, bond_type))

def get_atom_type(atom: Atom, parent: Atoms) -> AtomType:
    if atom.type in simple_types.keys():
        return simple_types[atom.type]

    atom_bonds = get_atom_bonds(atom, parent)
    if atom.type == "C":
        if len(atom_bonds) >= 4 and all(get_bond_type(parent[i-1], parent[j-1]) == BondType.Single for i, j in atom_bonds):
            return AtomType.C3
        elif (
                len(atom_bonds) == 3 and
                all(acyclic_bond(parent[i-1], parent[j-1]) for i, j in atom_bonds) and
                all([other_atom(atom, parent[i-1], parent[j-1]).type == "N" for i, j in atom_bonds]) and
                all([len(other_atom_bonds(atom, parent[i-1], parent[j-1], parent)) == 2 for i, j in atom_bonds]) and
                sum(other_atom(parent[k-1], parent[k-1], parent[l-1]).type == "O" for k, l in [other_atom_bonds(atom, parent[i-1], parent[j-1], parent) for i, j in atom_bonds]) == 0
        ):
            return AtomType.CCat
        elif len(atom_bonds) >= 2 and sum(get_bond_type(parent[i-1], parent[j-1]) == BondType.Aromatic for i, j in atom_bonds) >= 2:
            return AtomType.CAr
        elif (len(atom_bonds) == 1 or len(atom_bonds) == 2) and sum(get_bond_type(parent[i-1], parent[j-1]) == BondType.Triple for i, j in atom_bonds) >= 1:
            return AtomType.C1
        return AtomType.C2
    elif atom.type == "O":
        if len(nonmet(atom, parent)) == 1:
            bonded_atom = other_atom(atom, parent[atom_bonds[0][0]-1], parent[atom_bonds[0][1]-1])
            bonded_atom_bonds = get_atom_bonds(bonded_atom, parent)
            if bonded_atom.type in ["C", "P"] and len(bonded_atom_bonds) == 3 and sum(other_atom(atom, parent[i-1], parent[j-1]).type == "O" for i, j in bonded_atom_bonds):
                return AtomType.OCO2
        elif len(atom_bonds) >= 2 and all(get_bond_type(parent[i-1], parent[j-1]) == BondType.Single for i, j in atom_bonds):
            return AtomType.O3
        return AtomType.O2
    elif atom.type == "N":
        if len(nonmet(atom, parent)) == 4 and n_bonds_of_type(atom, parent, BondType.Single) == len(atom_bonds):
            return AtomType.N4
        elif len(atom_bonds) >=2 and

    return AtomType.Dummy


class Mol2Atom(Atom):
    def __init__(self, ty: str, x: float, y: float, z: float, index: Optional[int] = None, parent: Optional[Atoms] = None, units: AtomicDistance = AtomicDistance.Angstroms, atom_type: Optional[AtomType] = None):
        super().__init__(ty, x, y, z, index, parent, units)
        self._atom_type = atom_type

    @property
    def atom_type(self):
        if self._atom_type is None:
            self._atom_type = get_atom_type(self, self.parent)
        return self._atom_type



non_metal_atoms = [
    "H",
    "D",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Si",
    "P",
    "S",
    "Cl",
    "As",
    "Se",
    "Br",
    "Te",
    "I",
    "At",
    "He",
    "Ne",
    "Ar",
    "Kr",
    "Xe",
    "Rn",
]


class Mol2(File, GeometryFile):
    def __init__(self, path: Path):
        File.__init__(self, path)
        GeometryFile.__init__(self)

        self.system_name = None
        self.natoms = None
        self.nbonds = None
        self.nsubstructures = None
        self.nfeatures = None
        self.nsets = None
        self.mol_type = None
        self.charge_type = None
        self.sybyl_status = None

    @classproperty
    def filetype(self) -> str:
        return '.mol2'

    def _read_file(self):
        with open(self.path, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                if '@<TRIPOS>MOLECULE' in line:
                    system_name = next(f).strip()

    def format(self):
        self.mol_type = MoleculeType.Small
        self.charge_type = ChargeType.NoCharges
        self.sybyl_status = SybylStatus.NONE

        for i, atom in enumerate(self.atoms):
            if not isinstance(atom, Mol2Atom):
                self.atoms[i] = Mol2Atom(atom.type, atom.x, atom.y, atom.z, index=atom.index, parent=self.atoms, units=atom.units)


    def write(self, path: Optional[Path] = None):
        self.format()
        b = bonds(self.atoms)

        path = path or self.path
        with open(path, 'w') as f:
            f.write(f"# Name: {GLOBALS.SYSTEM_NAME}\n")
            f.write(f"# Created by: {current_user()}\n")
            f.write(f"# Created on: {datetime.datetime.now()}\n")
            f.write("\n")
            f.write("@<TRIPOS>MOLECULE\n")
            f.write(f"{GLOBALS.SYSTEM_NAME}\n")
            f.write(f" {len(self.atoms)} {len(b)} 0 0 0\n")
            f.write(f"{self.mol_type.value}\n")
            f.write(f"{self.charge_type.value}\n")
            f.write(f"{self.sybyl_status.value}\n")
            f.write("\n")
            f.write("@<TRIPOS>ATOM\n")
            for atom in self.atoms:
                f.write(f"{atom.index:7d} {atom.type} {atom.x:12.7f} {atom.y:12.7f} {atom.z:12.7f} {atom.type} 1 {GLOBALS.SYSTEM_NAME}\n")
            f.write("@<TRIPOS>BOND\n")
            for i, (bi, bj) in enumerate(b):
                f.write(f"{i+1:7d} {bi:4d} {bj:4d}   1\n")
