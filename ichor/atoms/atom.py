import itertools as it
import re

import numpy as np

from .. import constants


class Atom:
    ang2bohr = 1.88971616463
    counter = it.count(1)

    def __init__(self, coordinate_line):
        self.atom_type = ""
        self.atom_number = next(Atom.counter)

        self.x = 0
        self.y = 0
        self.z = 0

        self.read_input(coordinate_line)

        self._bonds = []
        self._angles = []
        self._dihedrals = []
        self.__level = it.count(0)

        self.x_axis = None
        self.xy_plane = None

        self.features = []
        self.properties = None

    def read_input(self, coordinate_line):
        if isinstance(coordinate_line, str):
            find_atom = coordinate_line.split()
            self.atom_type = find_atom[0]
            coordinate_line = next(
                re.finditer(
                    r"(\s*[+-]?\d+.\d+([Ee][+-]?\d+)?){3}", coordinate_line
                )
            ).group()
            coordinate_line = re.finditer(
                r"[+-]?\d+.\d+([Ee][+-]?\d+)?", coordinate_line
            )
            self.x = float(next(coordinate_line).group())
            self.y = float(next(coordinate_line).group())
            self.z = float(next(coordinate_line).group())
        elif isinstance(coordinate_line, Atom):
            self = coordinate_line
        elif isinstance(coordinate_line, (list, tuple)):
            if len(coordinate_line) == 3:
                self.atom_type = "H"
                self.x = float(coordinate_line[0])
                self.y = float(coordinate_line[1])
                self.z = float(coordinate_line[2])
            elif len(coordinate_line) == 4:
                self.atom_type = coordinate_line[0]
                self.x = float(coordinate_line[1])
                self.y = float(coordinate_line[2])
                self.z = float(coordinate_line[3])

    def sq_dist(self, other):
        return sum(
            (icoord - jcoord) ** 2
            for icoord, jcoord in zip(self.coordinates, other.coordinates)
        )

    def dist(self, other):
        return np.sqrt(self.sq_dist(other))

    def xdiff(self, other):
        return other.x - self.x

    def ydiff(self, other):
        return other.y - self.y

    def zdiff(self, other):
        return other.z - self.z

    def vec_to(self, other):
        return [self.xdiff(other), self.ydiff(other), self.zdiff(other)]

    def angle(self, atom1, atom2):
        temp = (
            self.xdiff(atom1) * self.xdiff(atom2)
            + self.ydiff(atom1) * self.ydiff(atom2)
            + self.zdiff(atom1) * self.zdiff(atom2)
        )
        return np.arccos((temp / (self.dist(atom1) * self.dist(atom2))))

    def set_bond(self, jatom):
        # self--jatom
        if jatom not in self._bonds:
            self._bonds.append(jatom)

    def set_angle(self, jatom):
        # jatom--self--katom
        if jatom not in self._angles:
            self._angles += [jatom]

    def set_dihedral(self, jatom):
        # jatom--self--katom--latom
        if jatom not in self._dihedrals:
            self._dihedrals += [jatom]

    def get_priorty(self, level):
        from .atoms import Atoms

        atoms = Atoms(self)
        for _ in range(level):
            atoms_to_add = []
            for atom in atoms:
                for bonded_atom in atom.bonds:
                    if bonded_atom not in atoms:
                        atoms_to_add.append(bonded_atom)
            atoms.add(atoms_to_add)
        return atoms.priority

    def reset_level(self):
        self.__level = it.count(0)

    def add_alf_atom(self, atom):
        if self.x_axis is None:
            self.x_axis = atom
        else:
            self.xy_plane = atom

    def C_1k(self):
        return [
            self.xdiff(self.x_axis) / self.dist(self.x_axis),
            self.ydiff(self.x_axis) / self.dist(self.x_axis),
            self.zdiff(self.x_axis) / self.dist(self.x_axis),
        ]

    def C_2k(self):
        xdiff1 = self.xdiff(self.x_axis)
        ydiff1 = self.ydiff(self.x_axis)
        zdiff1 = self.zdiff(self.x_axis)

        xdiff2 = self.xdiff(self.xy_plane)
        ydiff2 = self.ydiff(self.xy_plane)
        zdiff2 = self.zdiff(self.xy_plane)

        sigma_fflux = -(
            xdiff1 * xdiff2 + ydiff1 * ydiff2 + zdiff1 * zdiff2
        ) / (xdiff1 * xdiff1 + ydiff1 * ydiff1 + zdiff1 * zdiff1)

        y_vec1 = sigma_fflux * xdiff1 + xdiff2
        y_vec2 = sigma_fflux * ydiff1 + ydiff2
        y_vec3 = sigma_fflux * zdiff1 + zdiff2

        yy = np.sqrt(y_vec1 * y_vec1 + y_vec2 * y_vec2 + y_vec3 * y_vec3)

        y_vec1 /= yy
        y_vec2 /= yy
        y_vec3 /= yy

        return [y_vec1, y_vec2, y_vec3]

    def C_3k(self, C_1k, C_2k):
        xx3 = C_1k[1] * C_2k[2] - C_1k[2] * C_2k[1]
        yy3 = C_1k[2] * C_2k[0] - C_1k[0] * C_2k[2]
        zz3 = C_1k[0] * C_2k[1] - C_1k[1] * C_2k[0]

        return [xx3, yy3, zz3]

    def calculate_features(self, atoms, unit="bohr"):
        ang2bohr = Atom.ang2bohr
        if "ang" in unit.lower():
            ang2bohr = 1.0

        x_bond = self.dist(self.x_axis)
        xy_bond = self.dist(self.xy_plane)
        angle = self.angle(self.x_axis, self.xy_plane)

        self.features += [x_bond * ang2bohr]
        self.features += [xy_bond * ang2bohr]
        self.features += [angle]

        for jatom in atoms:
            if jatom.num in self.alf_nums:
                continue
            self.features += [self.dist(jatom) * ang2bohr]

            C_1k = self.C_1k()
            C_2k = self.C_2k()
            C_3k = self.C_3k(C_1k, C_2k)

            xdiff = self.xdiff(jatom)
            ydiff = self.ydiff(jatom)
            zdiff = self.zdiff(jatom)

            zeta1 = C_1k[0] * xdiff + C_1k[1] * ydiff + C_1k[2] * zdiff
            zeta2 = C_2k[0] * xdiff + C_2k[1] * ydiff + C_2k[2] * zdiff
            zeta3 = C_3k[0] * xdiff + C_3k[1] * ydiff + C_3k[2] * zdiff

            # Calculate Theta
            self.features += [np.arccos(zeta3 / self.dist(jatom))]

            # Calculate Phi
            self.features += [np.arctan2(zeta2, zeta1)]

    def to_angstroms(self):
        self.x /= Atom.ang2bohr
        self.y /= Atom.ang2bohr
        self.z /= Atom.ang2bohr

    def to_bohr(self):
        self.x *= Atom.ang2bohr
        self.y *= Atom.ang2bohr
        self.z *= Atom.ang2bohr

    @property
    def priority(self):
        level = next(self.__level)
        return self.get_priorty(level)

    @property
    def bonds(self):
        from .atoms import Atoms

        return Atoms(self._bonds)

    @property
    def bond_list(self):
        return [atom.atom_number - 1 for atom in self._bonds]

    @property
    def angle_list(self):
        return [atom.atom_number - 1 for atom in self._angles]

    @property
    def mass(self):
        return constants.type2mass[self.atom_type]

    @property
    def radius(self):
        return constants.type2rad[self.atom_type]

    @property
    def coordinates(self):
        return [self.x, self.y, self.z]

    @property
    def atom_num(self):
        return f"{self.atom_type}{self.atom_number}"

    @property
    def atom(self):
        return f"{self.atom_type}"

    @property
    def atom_num_coordinates(self):
        return [self.atom_num] + self.coordinates

    @property
    def atom_coordinates(self):
        return [self.atom] + self.coordinates

    @property
    def coordinates_string(self):
        width = str(16)
        precision = str(8)
        return f"{self.x:{width}.{precision}f}{self.y:{width}.{precision}f}{self.z:{width}.{precision}f}"

    @property
    def num(self):
        return self.atom_number

    @property
    def type(self):
        return self.atom_type

    @property
    def alf(self):
        alf = [self]
        if self.x_axis is not None:
            alf.append(self.x_axis)
        if self.xy_plane is not None:
            alf.append(self.xy_plane)
        return alf

    @property
    def alf_nums(self):
        return [atom.num for atom in self.alf]

    def __getattr__(self, attr):
        try:
            return self.__dict__[attr]
        except KeyError:
            try:
                return getattr(self.properties, attr)
            except AttributeError:
                raise AttributeError(f"Cannot find attribute '{attr}'")

    def __str__(self):
        return f"{self.atom_type:<3s}{self.coordinates_string}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if type(other) == Atom:
            return self.atom_num == other.atom_num
        elif type(other) == int:
            return self.atom_num == other
        else:
            raise ValueError(
                f"Cannot compare type({type(other)}) with type({type(self)})"
            )

    def __hash__(self):
        return hash(str(self.num) + str(self.coordinates_string))

    def __sub__(self, other):
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z
        return self
