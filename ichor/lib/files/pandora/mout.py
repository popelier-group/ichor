import re
from abc import ABC
from collections import namedtuple
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from ichor.atoms import Atom, Atoms
from ichor.common.functools import classproperty
from ichor.common.types import VarReprMixin
from ichor.files.file import File, FileContents
from ichor.files.geometry import AtomicDict, GeometryDataFile, GeometryFile
from ichor.lib.units import AtomicDistance

Quadrature = namedtuple("Quadrature", ["rad", "theta", "phi"])


def read_cp(
    f,
    xs: List[float],
    ys: List[float],
    zs: List[float],
    rhos: List[float],
    laps: List[float],
    lam1s: List[float],
    lam2s: List[float],
    lam3s: List[float],
    line=None,
):
    if line is None:
        line = next(f)
    xs += [float(x) for x in line.split("=")[-1].split()]  # x
    ys += [float(y) for y in next(f).split("=")[-1].split()]  # y
    zs += [float(z) for z in next(f).split("=")[-1].split()]  # z
    _ = next(f)  # blank line
    rhos += [float(rho) for rho in next(f).split("=")[-1].split()]  # RHO
    laps += [float(lap) for lap in next(f).split("=")[-1].split()]  # LAP
    _ = next(f)  # blank line
    lam1s += [float(lam1) for lam1 in next(f).split("=")[-1].split()]  # lam(1)
    lam2s += [float(lam2) for lam2 in next(f).split("=")[-1].split()]  # lam(2)
    lam3s += [float(lam3) for lam3 in next(f).split("=")[-1].split()]  # lam(3)

    return (
        xs,
        ys,
        zs,
        rhos,
        laps,
        lam1s,
        lam2s,
        lam3s,
    )


def read_bcp(
    f,
    atom_names: List[Tuple[str, str]],
    xs: List[float],
    ys: List[float],
    zs: List[float],
    rhos: List[float],
    laps: List[float],
    lam1s: List[float],
    lam2s: List[float],
    lam3s: List[float],
    ellips: List[float],
    K_rs: List[float],
    G_rs: List[float],
    eig1xs: List[float],
    eig1ys: List[float],
    eig1zs: List[float],
    eig2xs: List[float],
    eig2ys: List[float],
    eig2zs: List[float],
    eig3xs: List[float],
    eig3ys: List[float],
    eig3zs: List[float],
    dAs: List[float],
    dBs: List[float],
    pAs: List[float],
    pBs: List[float],
):
    line = next(f)  # n1-n2
    indices = line.split("=")[-1]
    bcp_indices = [
        (
            int(record.split("-")[0]),
            int(record.split("-")[1]),
        )
        for record in re.findall(r"\s+\d+-\s+\d+", indices)
    ]

    line = next(f)  # A - B
    types = line.split("=")[-1]
    bcp_types = [
        (
            record.split("-")[0].strip(),
            record.split("-")[1].strip(),
        )
        for record in re.findall(r"\s*\w+\s*-\s*\w+", types)
    ]

    atom_names += [
        (f"{ty[0]}{idx[0]}", f"{ty[1]}{idx[1]}")
        for ty, idx in zip(bcp_types, bcp_indices)
    ]

    (xs, ys, zs, rhos, laps, lam1s, lam2s, lam3s,) = read_cp(
        f,
        xs,
        ys,
        zs,
        rhos,
        laps,
        lam1s,
        lam2s,
        lam3s,
    )

    _ = next(f)  # blank line
    ellips += [
        float(ellip) for ellip in next(f).split("=")[-1].split()
    ]  # ellip
    K_rs += [float(kr) for kr in next(f).split("=")[-1].split()]  # K(r)
    G_rs += [float(gr) for gr in next(f).split("=")[-1].split()]  # G(r)
    _ = next(f)  # blank line
    eig1xs += [
        float(eig1x) for eig1x in next(f).split("=")[-1].split()
    ]  # eig1(x)
    eig1ys += [
        float(eig1y) for eig1y in next(f).split("=")[-1].split()
    ]  # eig1(y)
    eig1zs += [
        float(eig1z) for eig1z in next(f).split("=")[-1].split()
    ]  # eig1(z)
    _ = next(f)  # blank line
    eig2xs += [
        float(eig2x) for eig2x in next(f).split("=")[-1].split()
    ]  # eig2(x)
    eig2ys += [
        float(eig2y) for eig2y in next(f).split("=")[-1].split()
    ]  # eig2(y)
    eig2zs += [
        float(eig2z) for eig2z in next(f).split("=")[-1].split()
    ]  # eig2(z)
    _ = next(f)  # blank line
    eig3xs += [
        float(eig3x) for eig3x in next(f).split("=")[-1].split()
    ]  # eig3(x)
    eig3ys += [
        float(eig3y) for eig3y in next(f).split("=")[-1].split()
    ]  # eig3(y)
    eig3zs += [
        float(eig3z) for eig3z in next(f).split("=")[-1].split()
    ]  # eig3(z)
    _ = next(f)  # blank line
    dAs += [float(dA) for dA in next(f).split("=")[-1].split()]  # d(*-A)
    dBs += [float(dB) for dB in next(f).split("=")[-1].split()]  # d(*-B)
    pAs += [float(pA) for pA in next(f).split("=")[-1].split()]  # %(*-A)
    pBs += [float(pB) for pB in next(f).split("=")[-1].split()]  # %(*-B)

    return (
        atom_names,
        xs,
        ys,
        zs,
        rhos,
        laps,
        lam1s,
        lam2s,
        lam3s,
        ellips,
        K_rs,
        G_rs,
        eig1xs,
        eig1ys,
        eig1zs,
        eig2xs,
        eig2ys,
        eig2zs,
        eig3xs,
        eig3ys,
        eig3zs,
        dAs,
        dBs,
        pAs,
        pBs,
    )


def read_ncp(
    f,
    atom_names,
    dNs,
):
    line = next(f)
    cpdn = []
    cpan = []
    while line.startswith("d(*-N)"):
        record = line.split("=")[-1].split()
        dn = [float(record[i]) for i in range(0, len(record) - 2, 3)]
        an = [
            f"{record[i]}{int(record[i + 1])}"
            for i in range(1, len(record) - 1, 3)
        ]

        if not cpdn:
            for _ in range(len(dn)):
                cpdn.append([])
                cpan.append([])

        for i, (dni, ani) in enumerate(zip(dn, an)):
            cpdn[i].append(dni)
            cpan[i].append(ani)

        line = next(f)

    cpan = [tuple(an) for an in cpan]
    cpdn = [tuple(dn) for dn in cpdn]

    atom_names += cpan
    dNs += cpdn

    return (
        atom_names,
        dNs,
        line,
    )


def read_cp_and_ncp(
    f,
    atom_names,
    xs,
    ys,
    zs,
    rhos,
    laps,
    lam1s,
    lam2s,
    lam3s,
    dNs,
    line=None,
):
    (xs, ys, zs, rhos, laps, lam1s, lam2s, lam3s,) = read_cp(
        f,
        xs,
        ys,
        zs,
        rhos,
        laps,
        lam1s,
        lam2s,
        lam3s,
        line=line,
    )

    (atom_names, dNs, line,) = read_ncp(
        f,
        atom_names,
        dNs,
    )

    return (
        atom_names,
        xs,
        ys,
        zs,
        rhos,
        laps,
        lam1s,
        lam2s,
        lam3s,
        dNs,
        line,
    )


def read_rcp(
    f,
    atom_names,
    xs,
    ys,
    zs,
    rhos,
    laps,
    lam1s,
    lam2s,
    lam3s,
    dNs,
    line=None,
):
    return read_cp_and_ncp(
        f,
        atom_names,
        xs,
        ys,
        zs,
        rhos,
        laps,
        lam1s,
        lam2s,
        lam3s,
        dNs,
        line=line,
    )


def read_ccp(
    f,
    atom_names,
    xs,
    ys,
    zs,
    rhos,
    laps,
    lam1s,
    lam2s,
    lam3s,
    dNs,
    line=None,
):
    return read_cp_and_ncp(
        f,
        atom_names,
        xs,
        ys,
        zs,
        rhos,
        laps,
        lam1s,
        lam2s,
        lam3s,
        dNs,
        line=line,
    )


class MOUT(GeometryFile, GeometryDataFile, AtomicDict):
    nnuc: Optional[int]
    nbcp: Optional[int]
    nrcp: Optional[int]
    nccp: Optional[int]

    bond_critical_points: Optional[List["BondCriticalPoint"]]
    ring_critical_points: Optional[List["RingCriticalPoint"]]
    cage_critical_points: Optional[List["CageCriticalPoint"]]

    def __init__(self, path: Path):
        GeometryFile.__init__(self, path)
        GeometryDataFile.__init__(self)

        self.nnuc = FileContents
        self.nbcp = FileContents
        self.nrcp = FileContents
        self.nccp = FileContents

        self.bond_critical_points = FileContents
        self.ring_critical_points = FileContents
        self.cage_critical_points = FileContents

    def _read_file(self):
        with open(self.path, "r") as f:
            for line in f:
                if "-----  WAVE ------" in line:
                    self.atoms = Atoms()
                    _ = next(f)  # We are using a wfn and 2PDM from PySCF
                    _ = next(f)  # - - - - WAVEFUNCTION 1 - - - -
                    _ = next(f)  # filename
                    _ = next(f)  # title
                    _ = next(f)  # wavefunction header
                    _ = next(f)  # Cartesian Coordinates:
                    line = next(f)
                    while "center" in line:
                        record = line.split()
                        self.atoms.add(
                            AtomicMorfiOutput(
                                record[0],
                                float(record[3]),
                                float(record[4]),
                                float(record[5]),
                                units=AtomicDistance.Bohr,
                            )
                        )
                        line = next(f)
                    self.atoms.to_angstroms()

                if "Information for each atom :" in line:
                    _ = next(f)  # # quad inside beta     # quad outside beta
                    _ = next(
                        f
                    )  #  rad   theta    phi      rad   theta   phi      rho     maxsect
                    line = next(f)
                    while "Atom" in line:
                        record = line.split()
                        atom_name = f"{record[2]}{record[1]}"
                        self[atom_name].quadin = Quadrature(
                            int(record[3]), int(record[4]), int(record[5])
                        )
                        self[atom_name].quadout = Quadrature(
                            int(record[6]), int(record[7]), int(record[8])
                        )
                        self[atom_name].rho = float(record[9])
                        self[atom_name].maxsect = int(record[10])
                        line = next(f)

                if "Poincare-Hoft terms" in line:
                    self.nnuc = int(next(f).split()[-1])
                    self.nbcp = int(next(f).split()[-1])
                    self.nrcp = int(next(f).split()[-1])
                    self.nccp = int(next(f).split()[-1])

                    self.bond_critical_points = [
                        BondCriticalPoint() for _ in range(self.nbcp)
                    ]
                    self.ring_critical_points = [
                        RingCriticalPoint() for _ in range(self.nrcp)
                    ]
                    self.cage_critical_points = [
                        CageCriticalPoint() for _ in range(self.nccp)
                    ]

                if "Maximum critical points" in line:
                    _ = next(f)  # blank line
                    _ = next(f)  # ---- Bond critical points ----
                    line = next(f)
                    if "BCP" in line:
                        atom_names = []
                        xs = []
                        ys = []
                        zs = []
                        rhos = []
                        laps = []
                        lam1s = []
                        lam2s = []
                        lam3s = []
                        ellips = []
                        K_rs = []
                        G_rs = []
                        eig1xs = []
                        eig1ys = []
                        eig1zs = []
                        eig2xs = []
                        eig2ys = []
                        eig2zs = []
                        eig3xs = []
                        eig3ys = []
                        eig3zs = []
                        dAs = []
                        dBs = []
                        pAs = []
                        pBs = []
                        for _ in range(0, self.nbcp, 6):
                            (
                                atom_names,
                                xs,
                                ys,
                                zs,
                                rhos,
                                laps,
                                lam1s,
                                lam2s,
                                lam3s,
                                ellips,
                                K_rs,
                                G_rs,
                                eig1xs,
                                eig1ys,
                                eig1zs,
                                eig2xs,
                                eig2ys,
                                eig2zs,
                                eig3xs,
                                eig3ys,
                                eig3zs,
                                dAs,
                                dBs,
                                pAs,
                                pBs,
                            ) = read_bcp(
                                f,
                                atom_names,
                                xs,
                                ys,
                                zs,
                                rhos,
                                laps,
                                lam1s,
                                lam2s,
                                lam3s,
                                ellips,
                                K_rs,
                                G_rs,
                                eig1xs,
                                eig1ys,
                                eig1zs,
                                eig2xs,
                                eig2ys,
                                eig2zs,
                                eig3xs,
                                eig3ys,
                                eig3zs,
                                dAs,
                                dBs,
                                pAs,
                                pBs,
                            )
                            line = next(f)
                            while not line.strip():
                                line = next(f)

                        for i in range(self.nbcp):
                            self.bond_critical_points[i].A = self.atoms[
                                atom_names[i][0]
                            ]
                            self.bond_critical_points[i].B = self.atoms[
                                atom_names[i][1]
                            ]
                            self.bond_critical_points[i].pos = np.array(
                                [xs[i], ys[i], zs[i]]
                            )
                            self.bond_critical_points[i].rho = rhos[i]
                            self.bond_critical_points[i].lap = laps[i]
                            self.bond_critical_points[i].lam = np.array(
                                [lam1s[i], lam2s[i], lam3s[i]]
                            )
                            self.bond_critical_points[i].ellip = ellips[i]
                            self.bond_critical_points[i].K_r = K_rs[i]
                            self.bond_critical_points[i].G_r = G_rs[i]
                            self.bond_critical_points[i].eig = np.array(
                                [
                                    [eig1xs[i], eig1ys[i], eig1zs[i]],
                                    [eig2xs[i], eig2ys[i], eig2zs[i]],
                                    [eig3xs[i], eig3ys[i], eig3zs[i]],
                                ]
                            )
                            self.bond_critical_points[i].dA = dAs[i]
                            self.bond_critical_points[i].dB = dBs[i]
                            self.bond_critical_points[i].pA = pAs[i]
                            self.bond_critical_points[i].pB = pBs[i]

                    if "Ring critical points" in line:
                        line = next(f)  # blank line
                        if "Cage critical points" not in line:
                            _ = next(f)  # RCP #
                            atom_names = []
                            xs = []
                            ys = []
                            zs = []
                            rhos = []
                            laps = []
                            lam1s = []
                            lam2s = []
                            lam3s = []
                            dNs = []
                            for i in range(0, self.nrcp, 6):
                                (
                                    atom_names,
                                    xs,
                                    ys,
                                    zs,
                                    rhos,
                                    laps,
                                    lam1s,
                                    lam2s,
                                    lam3s,
                                    dNs,
                                    line,
                                ) = read_rcp(
                                    f,
                                    atom_names,
                                    xs,
                                    ys,
                                    zs,
                                    rhos,
                                    laps,
                                    lam1s,
                                    lam2s,
                                    lam3s,
                                    dNs,
                                )
                                # line = next(f)
                                # while not line.strip():
                                #     line = next(f)

                            for i in range(self.nrcp):
                                atoms = []
                                for atom in atom_names[i]:
                                    if atom in self.atoms.names:
                                        atoms.append(self.atoms[atom])
                                    else:
                                        atoms.append(
                                            Atom(
                                                "XX",
                                                0.0,
                                                0.0,
                                                0.0,
                                                parent=self.atoms,
                                                index=0,
                                            )
                                        )
                                self.ring_critical_points[
                                    i
                                ].atoms = atoms.copy()
                                self.ring_critical_points[i].pos = np.array(
                                    [xs[i], ys[i], zs[i]]
                                )
                                self.ring_critical_points[i].rho = rhos[i]
                                self.ring_critical_points[i].lap = laps[i]
                                self.ring_critical_points[i].lam = np.array(
                                    [lam1s[i], lam2s[i], lam3s[i]]
                                )
                                self.ring_critical_points[i].dN = dNs[i]

                    if "Cage critical points" in line:
                        line = next(f)
                        if "x" in line:
                            atom_names = []
                            xs = []
                            ys = []
                            zs = []
                            rhos = []
                            laps = []
                            lam1s = []
                            lam2s = []
                            lam3s = []
                            dNs = []
                            for i in range(0, self.nrcp, 6):
                                (
                                    atom_names,
                                    xs,
                                    ys,
                                    zs,
                                    rhos,
                                    laps,
                                    lam1s,
                                    lam2s,
                                    lam3s,
                                    dNs,
                                    line,
                                ) = read_ccp(
                                    f,
                                    atom_names,
                                    xs,
                                    ys,
                                    zs,
                                    rhos,
                                    laps,
                                    lam1s,
                                    lam2s,
                                    lam3s,
                                    dNs,
                                    line=line,
                                )

                        for i in range(self.nccp):
                            atoms = []
                            for atom in atom_names[i]:
                                if atom in self.atoms.names:
                                    atoms.append(self.atoms[atom])
                                else:
                                    atoms.append(
                                        Atom(
                                            "XX",
                                            0.0,
                                            0.0,
                                            0.0,
                                            parent=self.atoms,
                                            index=0,
                                        )
                                    )
                            self.cage_critical_points[i].atoms = atoms.copy()
                            self.cage_critical_points[i].pos = np.array(
                                [xs[i], ys[i], zs[i]]
                            )
                            self.cage_critical_points[i].rho = rhos[i]
                            self.cage_critical_points[i].lap = laps[i]
                            self.cage_critical_points[i].lam = np.array(
                                [lam1s[i], lam2s[i], lam3s[i]]
                            )
                            self.cage_critical_points[i].dN = dNs[i]

                if "INTEGRATION RESULTS" in line:
                    while "END OF OUTPUT" not in line:
                        line = next(f)
                        if "PySCF interaction energy" in line:
                            atom_index = int(line.split()[-1])
                            line = next(f)
                            interaction_energy = float(line.split()[-1])
                            self[
                                self.atoms[atom_index - 1].name
                            ].interaction_energy = interaction_energy

        for bcp in self.bond_critical_points:
            if not hasattr(self[bcp.A.name], "bond_critical_points"):
                self[bcp.A.name].bond_critical_points = []
            self[bcp.A.name].bond_critical_points.append(bcp)
            if not hasattr(self[bcp.B.name], "bond_critical_points"):
                self[bcp.B.name].bond_critical_points = []
            self[bcp.B.name].bond_critical_points.append(bcp)

        for rcp in self.ring_critical_points:
            for atom in rcp.atoms:
                if atom.name in self.atoms.atom_names:
                    if not hasattr(self[atom.name], "ring_critical_points"):
                        self[atom.name].ring_critical_points = []
                    self[atom.name].ring_critical_points.append(rcp)

        for ccp in self.cage_critical_points:
            for atom in ccp.atoms:
                if atom.name in self.atoms.atom_names:
                    if not hasattr(self[atom.name], "cage_critical_points"):
                        self[atom.name].cage_critical_points = []
                    self[atom.name].cage_critical_points.append(ccp)

    @classproperty
    def filetype(self) -> str:
        return ".mout"

    def items(self):
        return [(atom.name, atom) for atom in self.atoms]

    def __getitem__(self, item) -> "AtomicMorfiOutput":
        return self.atoms[item]


class AtomicMorfiOutput(Atom):
    quadin: Optional[Quadrature]
    quadout: Optional[Quadrature]
    rho: float
    maxsect: int
    interaction_energy: float = 0.0

    bond_critical_points: List["BondCriticalPoint"]
    ring_critical_points: List["RingCriticalPoint"]
    cage_critical_points: List["CageCriticalPoint"]

    def __self__(
        self,
        ty: str,
        x: float,
        y: float,
        z: float,
        quadin: Optional[Quadrature] = None,
        quadout: Optional[Quadrature] = None,
        rho: float = 0.0,
        maxsect: int = 1,
        interaction_energy=0.0,
        bcps: Optional[List["BondCriticalPoint"]] = None,
        rcps: Optional[List["RingCriticalPoint"]] = None,
        ccps: Optional[List["CageCriticalPoint"]] = None,
    ):
        super().__init__(ty, x, y, z)
        self.quadin = quadin
        self.quadout = quadout
        self.rho = rho
        self.maxsect = maxsect
        self.interaction_energy = interaction_energy

        self.bond_critical_points = bcps if bcps is not None else []
        self.ring_critical_points = rcps if rcps is not None else []
        self.cage_critical_points = ccps if ccps is not None else []


class CriticalPoint(VarReprMixin, ABC):
    def __init__(
        self,
        pos: np.ndarray = np.empty(3),
        rho: float = 0.0,
        lap: float = 0.0,
        lam: np.ndarray = np.empty(3),
    ):
        self.pos = pos
        self.rho = rho
        self.lap = lap
        self.lam = lam


class BondCriticalPoint(CriticalPoint):
    def __init__(
        self,
        A: Optional[Atom] = None,
        B: Optional[Atom] = None,
        pos: np.ndarray = np.empty(3),
        rho: float = 0.0,
        lap: float = 0.0,
        lam: np.ndarray = np.empty(3),
        ellip: float = 0.0,
        K_r: float = 0.0,
        G_r: float = 0.0,
        eig: np.ndarray = np.eye(3),
        dA: float = 0.0,
        dB: float = 0.0,
        pA: float = 0.0,
        pB: float = 0.0,
    ):
        super().__init__(pos, rho, lap, lam)

        self.A = A  # atom A
        self.B = B  # atom B

        self.ellip = ellip
        self.K_r = K_r
        self.G_r = G_r

        self.eig = eig

        self.dA = dA
        self.dB = dB
        self.pA = pA
        self.pB = pB


class NCriticalPoint(CriticalPoint):
    def __init__(
        self,
        atoms: Optional[List[Atom]] = None,
        pos: np.ndarray = np.empty(3),
        rho: float = 0.0,
        lap: float = 0.0,
        lam: np.ndarray = np.empty(3),
        dN: Optional[List[int]] = None,
    ):
        super().__init__(pos, rho, lap, lam)

        self.atoms = atoms if atoms is not None else []
        self.dN = dN if dN is not None else []


class RingCriticalPoint(NCriticalPoint):
    def __init__(
        self,
        atoms: Optional[List[Atom]] = None,
        pos: np.ndarray = np.empty(3),
        rho: float = 0.0,
        lap: float = 0.0,
        lam: np.ndarray = np.empty(3),
        dN: Optional[List[int]] = None,
    ):
        super().__init__(atoms, pos, rho, lap, lam, dN)


class CageCriticalPoint(NCriticalPoint):
    def __init__(
        self,
        atoms: Optional[List[Atom]] = None,
        pos: np.ndarray = np.empty(3),
        rho: float = 0.0,
        lap: float = 0.0,
        lam: np.ndarray = np.empty(3),
        dN: Optional[List[int]] = None,
    ):
        super().__init__(atoms, pos, rho, lap, lam, dN)
