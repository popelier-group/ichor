from ichor.analysis.dlpoly import dlpoly_menu
from ichor.analysis.rmse import rmse_menu
from ichor.analysis.s_curves import s_curve_menu
from ichor.menu import Menu


def analysis_menu():
    with Menu("Analysis Menu", space=True, back=True, exit=True) as menu:
        menu.add_option("s", "s-curve analysis", s_curve_menu)
        menu.add_option("rmse", "rmse analysis", rmse_menu)
        menu.add_option("dlpoly", "dlpoly analysis", dlpoly_menu)
