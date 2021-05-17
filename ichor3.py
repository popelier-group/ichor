from ichor.main import main_menu
from ichor.models import Models
from ichor.files import Trajectory
import numpy as np
from ichor.atoms import ListOfAtoms
from ichor.points import PointsDirectory
from ichor.adaptive_sampling.mepe import MEPE


if __name__ == '__main__':
    # main_menu()
    m = Models("LOG/WATER0059/")

    tr = Trajectory("WATER-3000.xyz")
    sp = PointsDirectory("SAMPLE_POOL")

    asm = MEPE(m)
    epe = asm(sp)
    print(epe)
    for p in epe:
        print(sp[p].path)
