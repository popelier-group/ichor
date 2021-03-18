from ICHOR import submit_gjfs
from ichor.menu import Menu
from ichor.debugging import printq


def submit_gjfs():
    printq("here")




def main_menu():
    with Menu("ICHOR Main Menu") as main_menu:
        main_menu.add_option("1", "Training Set Menu", submit_gjfs)


if __name__ == "__main__":
    main_menu()
