from ichor.main import main_menu
from ichor.models import Models
from ichor.files import Trajectory
import numpy as np
from ichor.atoms import ListOfAtoms


if __name__ == '__main__':
    # main_menu()
    m = Models("LOG/WATER0059/")
    tr = Trajectory("WATER-3000.xyz")

    print(m.predict(tr))

    # print(t["O1"])  # trajectory for one atom
    # print(t["O1"].features) # feature array trajectory for one atom

    # print(m.predict(tr[0]))
    # print(m[0, 2])

    # print(m.y[0])
    # print(m.predict(m.x[0]))

# class TrajectoryAtomView(Trajectory):
#     def __init__(self, atom_view):
#         for atom in atom_view:
#             self += [atom]
