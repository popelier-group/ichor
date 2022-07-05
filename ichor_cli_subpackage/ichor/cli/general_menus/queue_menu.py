from ichor.core.menu.menu import Menu
from ichor.hpc.batch_system.utils import delete_jobs, display_status_of_running_jobs



def queue_menu():
    """Handler function which opens up a menu containing options relating to jobs."""
    with Menu("Queue Meu") as menu:
        menu.add_option("del", "Delete currently running jobs", delete_jobs)
        menu.add_option(
            "stat",
            "Print status of currently running jobs",
            display_status_of_running_jobs,
            wait=True,
        )
