from dataclasses import dataclass, asdict

@dataclass
class MenuDescription:
    """ Dataclass for menu descriptions. The descriptions of new menus will be added here."""
    title: str
    prologue_text: str = ""
    epilogue_text: str = ""
    show_exit_option: bool = False

@dataclass
class MenuPrologue:

    def __str__(self):

        return "\n".join([f"{k} : {v}" for k, v in asdict(self).items()])

def update_menu_prologue(prologue):
    return str(prologue)
