import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, Union, Any

from ichor.core.atoms import Atom, Atoms
from ichor.core.common.functools import classproperty
from ichor.core.common.os import current_user
from ichor.core.files.file import File, WriteFile, ReadFile
from ichor.core.files.file_data import HasAtoms
from ichor.core.common.units import AtomicDistance


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
    Al = "Al"  # (aluminum)
    Br = "Br"  # (bromine)
    C1 = "C.1"  # (sp carbon)
    C2 = "C.2"  # (sp2 carbon)
    C3 = "C.3"  # (sp3 carbon)
    CAr = "C.ar"  # (aromatic carbon)
    CCat = "C.cat"  # (carbon)
    Ca = "Ca"  # (calcium)
    Cl = "Cl"  # (aromatic carbon)
    Dummy = "Du"  # (dummy atom-used as a placeholder)
    F = "F"  # (fluorine)
    H = "H"  # (hydrogen)
    HSPC = "H.spc"  # (hydrogen-water spc model)
    HT3P = "H.t3p"  # (hydrogen-water tip3p model)
    I = "I"  # (iodine)
    K = "K"  # (potassium)
    Li = "Li"  # (lithium)
    LonePair = "LP"  # (lone pair electrons)
    N1 = "N.1"  # (sp nitrogen)
    N2 = "N.2"  # (sp2 nitrogen)
    N3 = "N.3"  # (sp3 nitrogen)
    N4 = "N.4"  # (quaternary nitrogen)
    NAm = "N.am"  # (amide nitrogen)
    NAr = "N.ar"  # (aromatic nitrogen)
    NP13 = "N.p13"  # (trigonal nitrogen)
    Na = "Na"  # (sodium)
    O2 = "O.2"  # (sp2 oxygen)
    O3 = "O.3"  # (sp3 oxygen)
    OCO2 = "O.co2"  # (carboxy oxygen)
    OSPC = "O.spc"  # (oxygen-water spc model)
    OT3P = "O.t3p"  # (oxygen-water tip3p model)
    P3 = "P.3"  # (sp3 phosphorous)
    S2 = "S.2"  # (sp2 sulfur)
    S3 = "S.3"  # (sp3 sulfur)
    SO = "S.o"  # (sulfoxide sulfur)
    SO2 = "S.o2"  # (sulfone sulfur)
    Si = "Si"  # (silicon)
    CoOH = "Co.oh"  # (cobalt)
    RuOH = "Ru.oh"  # (Ruthenium)


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
    "Al": AtomType.Al,
    "Br": AtomType.Br,
    "Ca": AtomType.Ca,
    "Cl": AtomType.Cl,
    "F": AtomType.F,
    "H": AtomType.H,
    "I": AtomType.I,
    "K": AtomType.K,
    "Li": AtomType.Li,
    "Na": AtomType.Na,
    "Si": AtomType.Si,
}


portion_of_single_bond = {
    BondType.Single: 1,
    BondType.Aromatic: 0.92,
    BondType.Double: 0.87,
    BondType.Triple: 0.78,
}


def gasteigger_charge(atom: Atom) -> float:
    # todo: implement gasteigger charges
    return 0.0


def charge(atom: Atom) -> float:
    return gasteigger_charge(atom)


def get_valence(atom):
    return len(get_atom_bonds(atom))


def get_bond_type(atom1: Atom, atom2: Atom) -> BondType:
    if {atom1.type, atom2.type} == {"C", "N"}:
        # check for amide bond
        catom = atom1 if atom1.type == "C" else atom2
        natom = atom1 if atom1.type == "N" else atom2

        if (
            get_valence(catom) == 3
            and get_valence(natom) == 3
            and "O" in [atom.type for atom in get_bonded_atoms(catom)]
        ):
            return BondType.Amide

    atom1_valence = get_valence(atom1)
    atom2_valence = get_valence(atom2)
    if (
        atom1.unpaired_electrons == atom1_valence
        or atom2_valence == atom2.unpaired_electrons
    ):
        return BondType.Single
    if (
        atom1.valence - 1 == atom1_valence
        or atom2_valence - 1 == atom2.valence
    ):
        aromatic_types = ["C", "N"]
        if atom1.type in aromatic_types and atom2.type in aromatic_types:
            # check aromatic
            # _, in_ring = get_ring(atom1)

            if not acyclic_bond(atom1, atom2):
                return BondType.Aromatic

            single_bond_distance = atom1.radius + atom2.radius
            from ichor.core.analysis.geometry import calculate_bond

            bond_distance = calculate_bond(atom1.parent, atom1.i, atom2.i)
            bond_percentage = bond_distance / single_bond_distance
            if abs(
                bond_percentage - portion_of_single_bond[BondType.Aromatic]
            ) <= abs(
                bond_percentage - portion_of_single_bond[BondType.Double]
            ):
                return BondType.Aromatic

        return BondType.Double


visited = []


def _get_ring(
    atom: Atom,
    current_ring: List[Atom],
    called_from: Atom,
) -> Union[Tuple[Any, Any], Tuple[List[Atom], bool]]:
    bonded_atoms = get_bonded_atoms(atom)
    if len(bonded_atoms) > 1:
        for bonded_atom in bonded_atoms:
            if bonded_atom not in current_ring:
                ring, found = _get_ring(
                    bonded_atom, current_ring + [bonded_atom], atom
                )
                if found:
                    return ring, found
            if bonded_atom == current_ring[0] and bonded_atom != called_from:
                return current_ring, True
    return [current_ring[0]], False


def get_ring(atom):
    ring, found = _get_ring(atom, [atom], atom)
    return [a.name for a in ring], found


def acyclic_bond(atom1: Atom, atom2: Atom) -> bool:
    ring, found = get_ring(atom1)
    if found:
        return atom2.name not in ring
    return True


def bonds_of_type(atom, parent, bond_type):
    return [
        b
        for b in get_atom_bonds(atom)
        if get_bond_type(parent[b[0] - 1], parent[b[1] - 1]) is bond_type
    ]


def n_bonds_of_type(atom, parent, bond_type):
    return len(bonds_of_type(atom, parent, bond_type))


def get_bond_types(atom, parent) -> List[BondType]:
    return [
        get_bond_type(parent[i - 1], parent[j - 1])
        for i, j in get_atom_bonds(atom)
    ]


def other_atom(atom: Atom, atom1: Atom, atom2: Atom) -> Atom:
    """Return the other atom i.e. not 'atom' viev 2 atoms: 'atom1' and 'atom2'"""
    if atom.name == atom1.name:
        return atom2
    elif atom.name == atom2.name:
        return atom1
    else:
        raise ValueError(f"{atom} not in bond Bond({atom1}, {atom2})")


def bond_index_to_atom(
    bond: Tuple[int, int], parent: List[Atom]
) -> Tuple[Atom, Atom]:
    return parent[bond[0] - 1], parent[bond[1] - 1]


def get_atom_bonds(atom: Atom) -> List[Tuple[int, int]]:
    from ichor.core.analysis.geometry import bonds

    """Return list of bond indices (1-index)"""
    return [bond for bond in bonds(atom.parent) if atom.index in bond]


def get_bonded_atoms(atom: Atom) -> List[Atom]:
    """Return the atoms bonded to 'atom' from 'parent'"""
    return [
        other_atom(atom, *bond_index_to_atom(bond, atom.parent))
        for bond in get_atom_bonds(atom)
    ]


def other_atom_bonds(atom, atom1, atom2) -> List[Tuple[int, int]]:
    return get_atom_bonds(other_atom(atom, atom1, atom2))


def other_bonded_atoms(atom, atom1, atom2) -> List[Atom]:
    return get_bonded_atoms(other_atom(atom, atom1, atom2))


def nonmet(atom) -> List[Atom]:
    return [a for a in get_bonded_atoms(atom) if a.type in non_metal_atoms]


def get_atom_type(atom: Atom, parent: Atoms) -> AtomType:
    # sourcery skip: low-code-quality
    if atom.type in simple_types.keys():
        return simple_types[atom.type]

    atom_bonds = get_atom_bonds(atom)
    if atom.type == "C":
        if (
            4
            <= len(atom_bonds)
            == n_bonds_of_type(atom, parent, BondType.Single)
        ):
            return AtomType.C3
        elif (
            len(atom_bonds) == 3
            and all(
                acyclic_bond(parent[i - 1], parent[j - 1])
                for i, j in atom_bonds
            )
            and all(atom.type == "N" for atom in get_bonded_atoms(atom))
            and all(
                len(other_atom_bonds(atom, parent[i - 1], parent[j - 1])) == 2
                for i, j in atom_bonds
            )
            and sum(
                other_atom(parent[k - 1], parent[k - 1], parent[l - 1]).type
                == "O"
                for k, l in [
                    other_atom_bonds(atom, parent[i - 1], parent[j - 1])
                    for i, j in atom_bonds
                ]
            )
            == 0
        ):
            return AtomType.CCat
        elif (
            len(atom_bonds) >= 2
            and sum(
                get_bond_type(parent[i - 1], parent[j - 1])
                == BondType.Aromatic
                for i, j in atom_bonds
            )
            >= 2
        ):
            return AtomType.CAr
        elif (
            len(atom_bonds) in {1, 2}
            and sum(
                get_bond_type(parent[i - 1], parent[j - 1]) == BondType.Triple
                for i, j in atom_bonds
            )
            >= 1
        ):
            return AtomType.C1
        return AtomType.C2
    elif atom.type == "O":
        if len(nonmet(atom)) == 1:
            bonded_atom = other_atom(
                atom,
                parent[atom_bonds[0][0] - 1],
                parent[atom_bonds[0][1] - 1],
            )
            bonded_atom_bonds = get_atom_bonds(bonded_atom)
            if (
                bonded_atom.type in ["C", "P"]
                and len(bonded_atom_bonds) == 3
                and sum(
                    other_atom(bonded_atom, parent[i - 1], parent[j - 1]).type
                    == "O"
                    for i, j in bonded_atom_bonds
                )
                >= 2
            ):
                return AtomType.OCO2
        elif len(atom_bonds) >= 2 and all(
            get_bond_type(parent[i - 1], parent[j - 1]) == BondType.Single
            for i, j in atom_bonds
        ):
            return AtomType.O3
        return AtomType.O2
    elif atom.type == "N":
        if len(nonmet(atom)) == 4 and n_bonds_of_type(
            atom, parent, BondType.Single
        ) == len(atom_bonds):
            return AtomType.N4
        elif (
            len(atom_bonds) >= 2
            and len(bonds_of_type(atom, parent, BondType.Aromatic)) >= 2
        ):
            return AtomType.NAr
        elif (
            len(nonmet(atom)) == 1
            and get_bond_type(atom, nonmet(atom)[0]) is BondType.Triple
        ):
            return AtomType.N1
        elif len(nonmet(atom)) == 2 and [
            get_bond_types(atom, nonmetatom) for nonmetatom in nonmet(atom)
        ] in [
            [BondType.Double, BondType.Double],
            [BondType.Single, BondType.Triple],
            [BondType.Triple, BondType.Single],
        ]:
            return AtomType.N1
        elif len(nonmet(atom)) == 3:
            for nonmetatom in nonmet(atom):
                if nonmetatom.type == "C":
                    for batom in get_bonded_atoms(nonmetatom):
                        if (
                            batom.type in ["O", "S"]
                            and get_bond_type(nonmetatom, batom)
                            is BondType.Double
                        ):
                            return AtomType.NAm
            for a in nonmet(atom):
                if get_bond_type(atom, a) is not BondType.Single:
                    return AtomType.NP13
            # todo: add other NP13 criteria
        return AtomType.N2

    # todo: add other atom types

    return AtomType.Dummy


class Mol2Atom(Atom):
    def __init__(
        self,
        ty: str,
        x: float,
        y: float,
        z: float,
        index: Optional[int] = None,
        parent: Optional[Atoms] = None,
        units: AtomicDistance = AtomicDistance.Angstroms,
        atom_type: Optional[AtomType] = None,
    ):
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


# todo?: Would it be useful to be able to read Mol2?
class Mol2(HasAtoms, WriteFile, File):
    
    def __init__(self, path: Union[Path, str], atoms: Optional[Atoms] = None):
        
        super(WriteFile, self).__init__(path)

        self.atoms = atoms
        self.system_name = None
        self.nbonds = None
        self.nsubstructures = None
        self.nfeatures = None
        self.nsets = None
        self.mol_type = None
        self.charge_type = None
        self.sybyl_status = None

    @classproperty
    def filetype(self) -> str:
        return ".mol2"

    def format(self):
        self.mol_type = MoleculeType.Small
        self.charge_type = ChargeType.NoCharges
        self.sybyl_status = SybylStatus.NONE

        for i, atom in enumerate(self.atoms):
            if not isinstance(atom, Mol2Atom):
                self.atoms[i] = Mol2Atom(
                    atom.type,
                    atom.x,
                    atom.y,
                    atom.z,
                    index=atom.index,
                    parent=self.atoms,
                    units=atom.units,
                )

    def _write_file(self, path: Path, system_name: str):
        from ichor.core.calculators.geometry_calculator import bonds

        self.format()
        b = bonds(self.atoms)

        with open(path, "w") as f:
            f.write(f"# Name: {system_name}\n")
            f.write(f"# Created by: {current_user()}\n")
            f.write(f"# Created on: {datetime.datetime.now()}\n")
            f.write("\n")
            f.write("@<TRIPOS>MOLECULE\n")
            f.write(f"{system_name}\n")
            f.write(f" {len(self.atoms)} {len(b)} 0 0 0\n")
            f.write(f"{self.mol_type.value}\n")
            f.write(f"{self.charge_type.value}\n")
            f.write(f"{self.sybyl_status.value}\n")
            f.write("\n")
            f.write("@<TRIPOS>ATOM\n")
            for atom in self.atoms:
                f.write(
                    f"{atom.index:7d} {atom.type} {atom.x:12.7f} {atom.y:12.7f} {atom.z:12.7f} {atom.atom_type.value:<6} 1 {system_name} {gasteigger_charge(atom):6.4f}\n"
                )
            f.write("@<TRIPOS>BOND\n")
            for i, (bi, bj) in enumerate(b):
                f.write(
                    f"{i+1:7d} {bi:4d} {bj:4d} {get_bond_type(self.atoms[bi-1], self.atoms[bj-1]).value:>4}\n"
                )
