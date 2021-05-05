from typing import List

from ichor.atoms import Atoms
from ichor.feature_calculator.feature_calculator import FeatureCalculator


class AtomLocalFrame:
    origin: int
    x_axis: int
    xy_plane: int

    def __init__(self):
        self.origin = None
        self.x_axis = None
        self.xy_plane = None


class AtomicLocalFrame(list):
    pass


class LocalFrameAtom(Atom):
    def __init__(self, atom):
        # ...
        pass


class LocalFrameAtoms(Atoms):
    def __init__(self, atoms: Atoms):
        super().__init__(atoms)

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


class AtomicLocalFrameFeatureCalculator(FeatureCalculator):
    alf: Optional[List[AtomLocalFrame]] = None

    def __init__(self, geometry: Atoms):
        # Calculates ALF
        if not AtomicLocalFrameFeatureCalculator.alf:
            for i, atom in enumerate(geometry):
                for _ in range(2):
                    queue = LocalFrameAtoms(atom.bonds - atom.alf)
                    if queue.empty:
                        for bonded_atom in atom.bonds:
                            queue.add(bonded_atom.bonds)
                        queue -= atom.alf
                    atom.add_alf_atom(queue.max_priority)

    @classmethod
    def calculate_features(cls, geometry):
        pass
