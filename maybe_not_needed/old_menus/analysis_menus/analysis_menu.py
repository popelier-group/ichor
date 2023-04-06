from ichor.cli.analysis_menus.dlpoly_menu import dlpoly_menu
from ichor.cli.analysis_menus.gaussian_optimisation_menu import \
    run_gauss_opt_menu
from ichor.cli.analysis_menus.geometry_analysis import \
    geometry_analysis_menu
from ichor.cli.analysis_menus.rmse_menu import rmse_menu
from ichor.cli.analysis_menus.s_curve_menu import s_curve_menu
from ichor.cli.general_menus.rotate_mol import rotate_mol_menu
from ichor.core.menu.menu import Menu


def analysis_menu():
    with Menu("Analysis Menu") as menu:
        menu.add_option("s", "s-curve analysis", s_curve_menu)
        menu.add_option("rmse", "rmse analysis", rmse_menu)
        menu.add_option("dlpoly", "dlpoly analysis", dlpoly_menu)
        menu.add_option(
            "opt", "geometry optimisation analysis", run_gauss_opt_menu
        )
        menu.add_option("rotate", "rotate-mol", rotate_mol_menu)
        menu.add_option("geom", "geometry analysis", geometry_analysis_menu)
