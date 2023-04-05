from consolemenu.items import SubmenuItem as ConsoleSubmenuItem
from consolemenu import ConsoleMenu as OriginalConsoleMenu
from typing import Dict, Any

class SubmenuItem(ConsoleSubmenuItem):

    def __init__(self, text, submenu, submenu_options:"MenuOptions"=None,
                 menu=None, **kwargs):
        super().__init__(text, submenu, menu=menu, **kwargs)
        self.submenu._submenu_options = submenu_options


class ConsoleMenu(OriginalConsoleMenu):

    def __init__(self,menu_options:"MenuOptions"=None,**kwargs):
        
        # append any MenuOptions instance for the menu when creating it
        self.menu_options = menu_options
        super().__init__(**kwargs)

        # list with "MenuOptions" coming
        # from all menus that are parents to this menu
        parent_menu_options = []

        parent = self.parent
        # if the currently open menu has a parent
        while parent is not None:
            # get the MenuOptions for the parent
            parent_menu_options.append(parent.menu_options)
            # move to "upper" parent
            parent = parent.parent
