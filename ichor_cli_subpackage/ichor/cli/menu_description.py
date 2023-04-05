from dataclasses import dataclass

@dataclass
class MenuDescription:
    """ Dataclass for menu descriptions. Each menu has its own description, which remains CONSTANT."""
    title: str
    subtitle: str = ""
    prologue_description_text: str = ""
    epilogue_description_text: str = ""
    show_exit_option: bool = False