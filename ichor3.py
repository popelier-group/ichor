"""Open the main menu for ICHOR when running `python ichor3.py`. From there, the user can select what jobs to run."""

from ichor.main import main_menu
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)  # matt_todo: why is this line needed, it did not exist before

if __name__ == '__main__':
    main_menu()
