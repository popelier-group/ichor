from .atom import Atom
import itertools as it
import numpy as np
from  functools import lru_cache


class Atoms:
    ALF = []

    def __init__(self, atoms=None):
        self._atoms = []
        self._connectivity = None
        self._centred = False
        self.finish()

        if atoms is not None:
            self.add(atoms)

    def add(self, atom):
        if isinstance(atom, Atom):
            self._atoms.append(atom)
        elif isinstance(atom, str):
            self.add(Atom(atom))
        elif isinstance(atom, (list, Atoms)):
            for a in atom:
                self.add(a)

    def finish(self):
        Atom.counter = it.count(1)
        self.set_alf()

    def connect(self, iatom, jatom):
        iatom.set_bond(jatom)
        jatom.set_bond(iatom)

    def to_angstroms(self):
        for atom in self:
            atom.to_angstroms()

    def to_bohr(self):
        for atom in self:
            atom.to_bohr()

    def calculate_alf(self):
        self.connectivity
        for iatom in self:
            for _ in range(2):
                queue = iatom.bonds - iatom.alf
                if queue.empty:
                    for atom in iatom.bonds:
                        queue.add(atom.bonds)
                    queue -= iatom.alf
                iatom.add_alf_atom(queue.max_priority)
        Atoms.ALF = self.alf
        self.set_alf()

    def set_alf(self):
        # self._atoms = sorted(self._atoms, key=lambda x: x.num)
        for atom, atom_alf in zip(self, Atoms.ALF):
            atom.x_axis = self[atom_alf[1] - 1]
            atom.xy_plane = self[atom_alf[2] - 1]

    def calculate_features(self):
        if not Atoms.ALF:
            self.calculate_alf()
        self.set_alf()
        for atom in self:
            atom.calculate_features(self)

    def centre(self, centre_atom=None):
        if isinstance(centre_atom, int):
            centre_atom = self[centre_atom]
        elif centre_atom is None:
            centre_atom = self.centroid

        for i, atom in enumerate(self):
            atom -= centre_atom

        self._centred = True

    def center(self, center_atom=None):
        self.centre(centre_atom=center_atom)

    def rotate(self, R):
        coordinates = R.dot(self.coordinates.T).T
        for atom, coordinate in zip(self, coordinates):
            atom.x = coordinate[0]
            atom.y = coordinate[1]
            atom.z = coordinate[2]

    def _rmsd(self, other):
        dist = 0
        for iatom, jatom in zip(self, other):
            dist += iatom.sq_dist(jatom)
        return np.sqrt(dist / len(self))

    def rmsd(self, other):
        if not self._centred:
            self.centre()
        if not other._centred:
            other.centre()

        P = self.coordinates
        Q = other.coordinates
        H = self.coordinates.T.dot(other.coordinates)

        V, S, W = np.linalg.svd(H)
        d = (np.linalg.det(V) * np.linalg.det(W)) < 0.0

        if d:
            S[-1] = -S[-1]
            V[:, -1] = -V[:, -1]

        R = np.dot(V, W)

        other.rotate(R)
        return self._rmsd(other)

    @property
    def coordinates(self):
        return np.array([atom.coordinates for atom in self])

    @property
    def centroid(self):
        coordinates = self.coordinates.T

        x = np.mean(coordinates[0])
        y = np.mean(coordinates[1])
        z = np.mean(coordinates[2])

        return Atom([x, y, z])

    @property
    def priority(self):
        return sum(self.masses)

    @property
    def max_priority(self):
        prev_priorities = []
        while True:
            priorities = [atom.priority for atom in self]
            if (
                priorities.count(max(priorities)) == 1
                or prev_priorities == priorities
            ):
                break
            else:
                prev_priorities = priorities
        for atom in self:
            atom.reset_level()
        return self[priorities.index(max(priorities))]

    @property
    def masses(self):
        return [atom.mass for atom in self]

    @property
    def atoms(self):
        return [atom.atom_num for atom in self]

    @property
    def empty(self):
        return len(self) == 0

    @property
    @lru_cache()
    def connectivity(self):
        connectivity = np.zeros((len(self), len(self)))
        for i, iatom in enumerate(self):
            for j, jatom in enumerate(self):
                if iatom != jatom:
                    max_dist = 1.2 * (iatom.radius + jatom.radius)

                    if iatom.dist(jatom) < max_dist:
                        connectivity[i][j] = 1
                        self.connect(iatom, jatom)

        return connectivity

    @property
    def alf(self):
        return [[iatom.num for iatom in atom.alf] for atom in self]

    @property
    def features(self):
        try:
            return self._features
        except AttributeError:
            self.calculate_features()
            self._features = [atom.features for atom in self]
            return self._features

    @property
    def features_dict(self):
        try:
            return self._features_dict
        except AttributeError:
            self.calculate_features()
            self._features = {atom.atom_num: atom.features for atom in self}
            return self._features

    @property
    def types(self):
        return list(set([atom.type for atom in self]))

    def __len__(self):
        return len(self._atoms)

    def __delitem__(self, i):
        del self._atoms[i]

    def __getitem__(self, i):
        # TODO: fix this
        # if isinstance(i, INT):
        #     i = self.atoms.index(i.atom)
        return self._atoms[i]

    def __str__(self):
        return "\n".join([str(atom) for atom in self])

    def __repr__(self):
        return str(self)

    def __sub__(self, other):
        # other = sorted(Atoms(other), key=lambda x: x.num, reverse=False)
        for i, atom in enumerate(self):
            for jatom in other:
                if jatom == atom:
                    del self[i]
        return self

    def __bool__(self):
        return bool(self.atoms)