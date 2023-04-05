from dataclasses import dataclass

@dataclass
class MenuDescription:
    """ Dataclass for menu descriptions. Each menu has its own description, which remains CONSTANT."""
    title: str
    subtitle: str = ""
    prologue_description_text: str = ""
    epilogue_description_text: str = ""
    # note that the exit option becomes f"Return to {parent_menu}" for child menus.
    # Setting this to false means you cannot get back to parent menus from child menus.
    show_exit_option: bool = True