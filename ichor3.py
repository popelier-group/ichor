"""Open the main menu for ICHOR when running `python ichor3.py`. From there, the user can select what jobs to run."""
from ichor.main import main_menu
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)  # regex string in WFN.read() issues warning of recurssive group, will likely change WFN parsing in future and remove this

if __name__ == '__main__':
    main_menu()
