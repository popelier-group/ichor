from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

from ichor.analysis.predictions import get_true_predicted
from ichor.models import ModelsResult, Models
from ichor.points import PointsDirectory

from ichor.analysis.excel import num2col


def percentile(n: int) -> np.ndarray:
    return np.linspace(100 / n, 100, n)


def calculate_s_curves(
    model_location: Path,
    validation_set_location: Path,
    atoms: Optional[List[str]] = None,
    types: Optional[List[str]] = None,
):
    model = Models(model_location)
    validation_set = PointsDirectory(validation_set_location)
    true, predicted = get_true_predicted(
        model, validation_set, atoms, types
    )
    write_to_excel(true, predicted)


def write_to_excel(
    true: ModelsResult,
    predicted: ModelsResult,
    output: Path = "s-curves.xlsx",
):
    true = true.T
    predicted = predicted.T
    error = (true - predicted).abs()

    with pd.ExcelWriter(output) as writer:
        workbook = writer.book
        for type_ in true.keys():
            atom_sheets = {}
            for atom in true[type_].keys():
                data = {
                    "True": true[type_][atom],
                    "Predicted": predicted[type_][atom],
                    "Error": error[type_][atom],
                }
                df = pd.DataFrame(data)
                df.sort_values("Error", inplace=True)
                df["%"] = percentile(len(df["Error"]))
                sheet_name = f"{atom}_{type_}"
                atom_sheets[atom] = sheet_name
                df.to_excel(writer, sheet_name=sheet_name)
                s_curve = workbook.add_chart(
                    {"type": "scatter", "subtype": "straight"}
                )
                s_curve.add_series(
                    {
                        "categories": [sheet_name, 1, 3, len(df["Error"]), 3],
                        "values": [sheet_name, 1, 4, len(df["%"]), 4],
                        "line": {"width": 1.5},
                    }
                )
                s_curve.set_x_axis(
                    {
                        "name": "Prediction Error",
                        "log_base": 10,
                        "major_gridlines": {
                            "visible": True,
                            "line": {"width": 0.75, 'color': '#BFBFBF'},
                        },
                        "minor_gridlines": {
                            "visible": True,
                            "line": {"width": 0.75, 'color': '#F2F2F2'},
                        },
                    }
                )
                s_curve.set_y_axis(
                    {
                        "name": "%",
                        "min": 0,
                        "max": 100,
                        "major_gridlines": {
                            "visible": True,
                            "line": {"width": 0.75, 'color': '#BFBFBF'},
                        },
                    }
                )

                s_curve.set_legend({"position": "none"})
                s_curve.set_style(10)
                writer.sheets[sheet_name].insert_chart("G2", s_curve)

            df = pd.DataFrame(error[type_])
            df["Total"] = error[type_].reduce()
            df.sort_values("Total", inplace=True)
            ndata = len(df["Total"])
            df["%"] = percentile(ndata)
            sheet_name = f"Total_{type_}"
            df.to_excel(writer, sheet_name=sheet_name)

            atom_names = list(map(str, true[type_].keys()))

            total_s_curve = workbook.add_chart(
                {"type": "scatter", "subtype": "straight"}
            )
            total_s_curve.add_series(
                {
                    "categories": [sheet_name, 1, len(atom_names)+1, ndata, len(atom_names)+1],
                    "values": [sheet_name, 1, len(atom_names)+2, ndata, len(atom_names)+2],
                    "line": {"width": 1.5},
                }
            )
            total_s_curve.set_x_axis(
                {
                    "name": "Prediction Error",
                    "log_base": 10,
                    "major_gridlines": {
                        "visible": True,
                        "line": {"width": 0.75, 'color': '#BFBFBF'},
                    },
                    "minor_gridlines": {
                        "visible": True,
                        "line": {"width": 0.75, 'color': '#F2F2F2'},
                    },
                }
            )
            total_s_curve.set_y_axis(
                {
                    "name": "%",
                    "min": 0,
                    "max": 100,
                    "major_gridlines": {
                        "visible": True,
                        "line": {"width": 0.75, 'color': '#BFBFBF'},
                    },
                }
            )

            total_s_curve.set_legend({"position": "none"})
            total_s_curve.set_style(10)

            atomic_s_curve = workbook.add_chart(
                {"type": "scatter", "subtype": "straight"}
            )

            for atom_name in atom_names:
                atomic_s_curve.add_series(
                    {
                        "name": atom_name,
                        "categories": [atom_sheets[atom_name], 1, 3, ndata, 3],
                        "values": [atom_sheets[atom_name], 1, 4, ndata, 4],
                        "line": {"width": 1.5},
                    }
                )
            atomic_s_curve.set_x_axis(
                {
                    "name": "Prediction Error",
                    "log_base": 10,
                    "major_gridlines": {
                        "visible": True,
                        "line": {"width": 0.75, 'color': '#BFBFBF'},
                    },
                    "minor_gridlines": {
                        "visible": True,
                        "line": {"width": 0.75, 'color': '#F2F2F2'},
                    },
                }
            )
            atomic_s_curve.set_y_axis(
                {
                    "name": "%",
                    "min": 0,
                    "max": 100,
                    "major_gridlines": {
                        "visible": True,
                        "line": {"width": 0.75, 'color': '#BFBFBF'},
                    },
                }
            )

            atomic_s_curve.set_legend({"position": "right"})
            total_s_curve.set_style(10)

            writer.sheets[sheet_name].insert_chart(f"{num2col(len(atom_names)+5)}2", total_s_curve)
            writer.sheets[sheet_name].insert_chart(f"{num2col(len(atom_names)+5)}18", atomic_s_curve)
