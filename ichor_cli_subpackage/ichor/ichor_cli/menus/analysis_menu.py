from ichor.ichor_lib.analysis.dlpoly import dlpoly_menu
from ichor.ichor_lib.analysis.geometry import geometry_analysis_menu
from ichor.ichor_lib.analysis.opt import run_gauss_opt_menu
from ichor.ichor_menu.analysis.rmse import rmse_menu
from ichor.ichor_cli.menus.rotate_mol import rotate_mol_menu
from ichor.ichor_cli.analysis.s_curves import s_curve_menu
from ichor.ichor_cli.menus.menu import Menu


def analysis_menu():
    with Menu("Analysis Menu", space=True, back=True, exit=True) as menu:
        menu.add_option("s", "s-curve analysis", s_curve_menu)
        menu.add_option("rmse", "rmse analysis", rmse_menu)
        menu.add_option("dlpoly", "dlpoly analysis", dlpoly_menu)
        menu.add_option(
            "opt", "geometry optimisation analysis", run_gauss_opt_menu
        )
        menu.add_option("rotate", "rotate-mol", rotate_mol_menu)
        menu.add_option("geom", "geometry analysis", geometry_analysis_menu)
