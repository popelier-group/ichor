from consolemenu.items import SubmenuItem as OriginalSubmenuItem
from consolemenu import ConsoleMenu as OriginalConsoleMenu
from typing import Dict, Any

# class SubmenuItem(OriginalSubmenuItem):

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)


class ConsoleMenu(OriginalConsoleMenu):

    def __init__(self, this_menu_options:"MenuOptions"=None, **kwargs):

        super().__init__(**kwargs)

        self.this_menu_options = this_menu_options

    @property
    def parent_menu_options(self):
        # list with "MenuOptions" of all parent classes
        # from all menus that are parents to this menu
        _parent_menu_options = []

        prnt = self.parent
        # while there is a parent menu
        while prnt is not None:
            # get the MenuOptions for the parent
            _parent_menu_options.append(prnt.this_menu_options)
            # move to "upper" parent
            prnt = prnt.parent

        # reverse ordering so that oldest parent options are at the top
        self._parent_menu_options = _parent_menu_options[::-1]
        return self._parent_menu_options

    def get_prologue_text(self):
        """ Gets the prologue text, containing information for saved variables that are needed for jobs.
        The 
        """

        # if there is some constant prologue text to be displayed for some menu for some reason
        # there really shouldn't be a need for this but keep for now
        prologue_txt = self.prologue_text() if callable(self.prologue_text) else self.prologue_text
        # add the strings that each parent gives
        for p_options in self.parent_menu_options:
            prologue_txt += p_options()
        # add a new line so that the current menu options are on a new line
        prologue_txt += "\n"
        # finally add any new options from the current menu
        if self.this_menu_options:
            prologue_txt += self.this_menu_options()

        return prologue_txt