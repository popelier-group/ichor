from ichor.main import main_menu
from ichor.files.trajectory import Trajectory


if __name__ == '__main__':
    # main_menu()
    t = Trajectory("WATER-3000.xyz")
    print(t[0])

    print(t[0]["H2"].features)