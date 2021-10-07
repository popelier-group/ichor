from ichor.files.file import File
from ichor.files.geometry import GeometryFile
from pathlib import Path
from enum import Enum
from ichor.atoms import Atom, Atoms
from ichor.units import AtomicDistance
from typing import Optional
from ichor.common.functools import classproperty


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


simple_types = {
    "D": AtomType.H,
    "P": AtomType.P3,
    "Co": AtomType.CoOH,
    "Ru": AtomType.RuOH,
}


class Mol2Atom(Atom):
    def __init__(self, ty: str, x: float, y: float, z: float, index: Optional[int] = None, parent: Optional[Atoms] = None, units: AtomicDistance = AtomicDistance.Angstroms):
        super().__init__(ty, x, y, z, index, parent, units)


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


