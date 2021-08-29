"""Contains all avalable settings for Gaussian, AIMALL, FEREBUS, as well as constant values that are used throughout ICHOR to make conversions, etc."""

import random
from typing import Dict, List

import numpy as np

from ichor.common.types import Version

# matt_todo: I think sticking to only 1 logo will be better for consistency. Someone might want to parse the file for some reason.
ichor_logo_1 = (
    "#############################################################################################################\n"
    "#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::#\n"
    "#::#######################################################################################################::#\n"
    "#::#                                                                                                     #::#\n"
    "#::#  IIIIIIIIII         CCCCCCCCCCCCC HHHHHHHHH     HHHHHHHHH      OOOOOOOOO      RRRRRRRRRRRRRRRRR     #::#\n"
    "#::#  I::::::::I      CCC::::::::::::C H:::::::H     H:::::::H    OO:::::::::OO    R::::::::::::::::R    #::#\n"
    "#::#  I::::::::I    CC:::::::::::::::C H:::::::H     H:::::::H  OO:::::::::::::OO  R::::::RRRRRR:::::R   #::#\n"
    "#::#  II::::::II   C:::::CCCCCCCC::::C HH::::::H     H::::::HH O:::::::OOO:::::::O RR:::::R     R:::::R  #::#\n"
    "#::#    I::::I    C:::::C       CCCCCC   H:::::H     H:::::H   O::::::O   O::::::O   R::::R     R:::::R  #::#\n"
    "#::#    I::::I   C:::::C                 H:::::H     H:::::H   O:::::O     O:::::O   R::::R     R:::::R  #::#\n"
    "#::#    I::::I   C:::::C                 H::::::HHHHH::::::H   O:::::O     O:::::O   R::::RRRRRR:::::R   #::#\n"
    "#::#    I::::I   C:::::C                 H:::::::::::::::::H   O:::::O     O:::::O   R:::::::::::::RR    #::#\n"
    "#::#    I::::I   C:::::C                 H:::::::::::::::::H   O:::::O     O:::::O   R::::RRRRRR:::::R   #::#\n"
    "#::#    I::::I   C:::::C                 H:::::H     H:::::H   O:::::O     O:::::O   R::::R     R:::::R  #::#\n"
    "#::#    I::::I   C:::::C                 H::::::HHHHH::::::H   O:::::O     O:::::O   R::::R     R:::::R  #::#\n"
    "#::#    I::::I    C:::::C       CCCCCC   H:::::H     H:::::H   O::::::O   O::::::O   R::::R     R:::::R  #::#\n"
    "#::#  II::::::II   C:::::CCCCCCCC::::C HH::::::H     H::::::HH O:::::::OOO:::::::O RR:::::R     R:::::R  #::#\n"
    "#::#  I::::::::I    CC:::::::::::::::C H:::::::H     H:::::::H  OO:::::::::::::OO  R::::::R     R:::::R  #::#\n"
    "#::#  I::::::::I      CCC::::::::::::C H:::::::H     H:::::::H    OO:::::::::OO    R::::::R     R:::::R  #::#\n"
    "#::#  IIIIIIIIII         CCCCCCCCCCCCC HHHHHHHHH     HHHHHHHHH      OOOOOOOOO      RRRRRRRR     RRRRRRR  #::#\n"
    "#::#                                                                                                     #::#\n"
    "#::#######################################################################################################::#\n"
    "#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::#\n"
)

ichor_logo_2 = (
    "###############################################\n"
    "#.####..######..##.....##..#######..########..#\n"
    "#..##..##....##.##.....##.##.....##.##.....##.#\n"
    "#..##..##.......##.....##.##.....##.##.....##.#\n"
    "#..##..##.......#########.##.....##.########..#\n"
    "#..##..##.......##.....##.##.....##.##...##...#\n"
    "#..##..##....##.##.....##.##.....##.##....##..#\n"
    "#.####..######..##.....##..#######..##.....##.#\n"
    "###############################################\n"
)

_ichor_logos = [
    ichor_logo_1,
    ichor_logo_2,
]

ichor_logo = random.choice(_ichor_logos)

BOAQ_VALUES: List[str] = [
    "auto",
    "gs1",
    "gs2",
    "gs3",
    "gs4",
    "gs5",
    "gs6",
    "gs7",
    "gs8",
    "gs9",
    "gs10",
    "gs15",
    "gs20",
    "gs25",
    "gs30",
    "gs35",
    "gs40",
    "gs45",
    "gs50",
    "gs55",
    "gs60",
    "leb23",
    "leb25",
    "leb27",
    "leb29",
    "leb31",
    "leb32",
]

IASMESH_VALUES: List[str] = [
    "sparse",
    "medium",
    "fine",
    "veryfine",
    "superfine",
]

GAUSSIAN_METHODS: List[str] = [
    "AM1",
    "PM3",
    "PM3MM",
    "PM6",
    "PDDG",
    "PM7",
    "HF",
    "CASSCF",
    "MP2",
    "MP3",
    "MP4(SDQ)",
    "MP4(SDQ,full)",
    "MP4(SDTQ)",
    "MP5",
    "BD",
    "CCD",
    "CCSD",
    "QCISD",
    "BD(T)",
    "CCSD(T)",
    "QCISD(T)",
    "BD(TQ)",
    "CCSD(TQ)",
    "QCISD(TQ)",
    "EPT",
    "CBS",
    "GN",
    "W1",
    "CIS",
    "TD",
    "EOM",
    "ZINDO",
    "DFTB",
    "CID",
    "CISD",
    "GVB",
    "S",
    "XA",
    "B",
    "PW91",
    "mPW",
    "G96",
    "PBE",
    "O",
    "TPSS",
    "BRx",
    "PKZB",
    "wPBEh",
    "PBEh",
    "VWN",
    "VWN5",
    "LYP",
    "PL",
    "P86",
    "PW91",
    "B95",
    "PBE",
    "TPSS",
    "KCIS",
    "BRC",
    "PKZB",
    "VP86",
    "V5LYP",
    "HFS",
    "XAlpha",
    "HFB",
    "VSXC",
    "HCTH",
    "HCTH93",
    "HCTH147",
    "HCTH407",
    "tHCTH",
    "M06L",
    "B97D",
    "B97D3",
    "SOGGA11",
    "M11L",
    "N12",
    "MN12L",
    "B3LYP",
    "B3P86",
    "B3PW91",
    "B1B95",
    "mPW1PW91",
    "mPW1LYP",
    "mPW1PBE",
    "mPW3PBE",
    "B98",
    "B971",
    "B972",
    "PBE1PBE",
    "B1LYP",
    "O3LYP",
    "BHandH",
    "BHandHLYP",
    "BMK",
    "M06",
    "M06HF",
    "M062X",
    "tHCTHhyb",
    "APFD",
    "APF",
    "SOGGA11X",
    "PBEh1PBE",
    "TPSSh",
    "X3LYP",
    "HSEH1PBE",
    "OHSE2PBE",
    "OHSE1PBE",
    "wB97XD",
    "wB97",
    "wB97X",
    "LC-wPBE",
    "CAM-B3LYP",
    "HISSbPBE",
    "M11",
    "N12SX",
    "MN12SX",
    "LC-",
]

AIMALL_FUNCTIONALS: List[str] = ["MO62X", "B3LYP", "PBE"]

FEREBUS_TYPES: List[str] = ["executable", "python"]

FEREBUS_LEGACY_CUTOFF: Version = Version("6.5.0")

KERNELS: List[str] = ["rbf", "rbf-cyclic"]

DLPOLY_LEGACY_CUTOFF: Version = Version("4.08")

type2mass: Dict[str, float] = {
    "H": 1.007825,
    "He": 4.002603,
    "Li": 7.016005,
    "Be": 9.012182,
    "B": 11.009305,
    "C": 12.0,
    "N": 14.003074,
    "O": 15.994915,
    "F": 18.998403,
    "Ne": 19.99244,
    "Na": 22.989769,
    "Mg": 23.985042,
    "Al": 26.981539,
    "Si": 27.976927,
    "P": 30.973762,
    "S": 31.972071,
    "Cl": 34.968853,
    "Ar": 39.962383,
    "K": 38.963707,
    "Ca": 39.962591,
    "Sc": 44.955912,
    "Ti": 47.947946,
    "V": 50.94396,
    "Cr": 51.940508,
    "Mn": 54.938045,
    "Fe": 55.9349382,
    "Co": 58.933195,
    "Ni": 57.935343,
    "Cu": 62.929598,
    "Zn": 63.929142,
    "Ga": 68.925574,
    "Ge": 73.921178,
    "As": 74.921597,
    "Se": 79.916521,
    "Br": 78.918337,
    "Kr": 83.911507,
}

type2rad: Dict[str, float] = {
    "H": 0.37,
    "He": 0.32,
    "Li": 1.34,
    "Be": 0.9,
    "B": 0.82,
    "C": 0.77,
    "N": 0.74,
    "O": 0.73,
    "F": 0.71,
    "Ne": 0.69,
    "Na": 1.54,
    "Mg": 1.3,
    "Al": 1.18,
    "Si": 1.11,
    "P": 1.06,
    "S": 1.02,
    "Cl": 0.99,
    "Ar": 0.97,
    "K": 1.96,
    "Ca": 1.74,
    "Sc": 1.44,
    "Ti": 1.36,
    "V": 1.25,
    "Cr": 1.27,
    "Mn": 1.39,
    "Fe": 1.25,
    "Co": 1.26,
    "Ni": 1.21,
    "Cu": 1.38,
    "Zn": 1.31,
    "Ga": 1.26,
    "Ge": 1.22,
    "As": 1.19,
    "Se": 1.16,
    "Br": 1.14,
    "Kr": 1.1,
}

type2valence: Dict[str, int] = {
    "H": 1,
    "He": 2,
    "Li": 3,
    "Be": 4,
    "B": 3,
    "C": 4,
    "N": 5,
    "O": 6,
    "F": 7,
    "Ne": 8,
    "Na": 9,
    "Mg": 10,
    "Al": 3,
    "Si": 4,
    "P": 5,
    "S": 6,
    "Cl": 7,
    "Ar": 8,
    "K": 9,
    "Ca": 10,
    "Sc": 11,
    "Ti": 12,
    "V": 13,
    "Cr": 14,
    "Mn": 15,
    "Fe": 16,
    "Co": 17,
    "Ni": 18,
    "Cu": 11,
    "Zn": 12,
    "Ga": 13,
    "Ge": 4,
    "As": 5,
    "Se": 6,
    "Br": 7,
    "Kr": 8,
    "Sr": 10,
    "Y": 11,
    "Zr": 12,
    "Mo": 14,
    "Ru": 16,
    "Rh": 17,
    "Pd": 18,
    "Ag": 11,
    "In": 13,
    "Sb": 5,
    "Te": 6,
    "I": 7,
    "Ba": 10,
    "Ce": 12,
    "Gd": 18,
    "W": 14,
    "Au": 11,
    "Bi": 5,
}

dlpoly_weights: Dict[str, float] = {
    "H": 1.007975,
    "He": 4.002602,
    "Li": 6.9675,
    "Be": 9.0121831,
    "B": 10.8135,
    "C": 12.0106,
    "N": 14.006855,
    "O": 15.9994,
    "F": 18.99840316,
    "Ne": 20.1797,
    "Na": 22.98976928,
    "Mg": 24.3055,
    "Al": 26.9815385,
    "Si": 28.085,
    "P": 30.973762,
    "S": 32.0675,
    "Cl": 35.4515,
    "Ar": 39.948,
    "K": 39.0983,
    "Ca": 40.078,
    "Sc": 44.955908,
    "Ti": 47.867,
    "V": 50.9415,
    "Cr": 51.9961,
    "Mn": 54.938044,
    "Fe": 55.845,
    "Co": 58.933194,
    "Ni": 58.6934,
    "Cu": 63.546,
    "Zn": 65.38,
    "Ga": 69.723,
    "Ge": 72.63,
    "As": 74.921595,
    "Se": 78.971,
    "Br": 79.904,
    "Kr": 83.798,
    "Rb": 85.4678,
    "Sr": 87.62,
    "Y": 88.90584,
    "Zr": 91.224,
    "Nb": 92.90637,
    "Mo": 95.95,
}

multipole_names: List[str] = [
    "q00",
    "q10",
    "q11c",
    "q11s",
    "q20",
    "q21c",
    "q21s",
    "q22c",
    "q22s",
    "q30",
    "q31c",
    "q31s",
    "q32c",
    "q32s",
    "q33c",
    "q33s",
    "q40",
    "q41c",
    "q41s",
    "q42c",
    "q42s",
    "q43c",
    "q43s",
    "q44c",
    "q44s",
]

# ha_to_kj_mol = 2625.5
ha_to_kj_mol: float = (
    2625.4996394799  # Taken from https://en.wikipedia.org/wiki/Hartree
)
# The wikipedia article is converted from https://physics.nist.gov/cgi-bin/cuu/Value?hr

bohr2ang = 0.529177210903  # Converted from https://physics.nist.gov/cgi-bin/cuu/Value?bohrrada0
ang2bohr = 1.0 / bohr2ang

rt3: float = np.sqrt(3)
rt5: float = np.sqrt(5)
rt6: float = np.sqrt(6)
rt10: float = np.sqrt(10)
rt15: float = np.sqrt(15)
rt35: float = np.sqrt(35)
rt70: float = np.sqrt(70)
rt1_24: float = np.sqrt(1 / 24)
rt_1_5: float = np.sqrt(1 / 5)
rt_1_10: float = np.sqrt(1 / 10)
rt_1_35: float = np.sqrt(1 / 35)
rt2_3: float = np.sqrt(2 / 3)
rt_2_35: float = np.sqrt(2 / 35)
rt3_3: float = np.sqrt(3) / 3
rt_3_3: float = np.sqrt(3) / 2
rt_3_5: float = np.sqrt(3 / 5)
rt3_8: float = np.sqrt(3 / 8)
rt5_8: float = np.sqrt(5 / 8)
rt5_12: float = np.sqrt(5 / 12)
rt_8_5: float = np.sqrt(8 / 5)
rt12_3: float = np.sqrt(12) / 3
