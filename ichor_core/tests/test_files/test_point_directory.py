from pathlib import Path

import numpy as np

from ichor.core.files import PointDirectory

from ichor.core.files.gaussian.gaussian_output import (
    MolecularDipole,
    MolecularHexadecapole,
    MolecularOctupole,
    MolecularQuadrupole,
    TracelessMolecularQuadrupole,
)

from tests.path import get_cwd

from tests.test_files import _compare_nested_dicts

example_dir = (
    get_cwd(__file__)
    / ".."
    / ".."
    / ".."
    / "example_files"
    / "example_points_directory"
    / "WATER_MONOMER.pointsdir"
    / "WATER_MONOMER0000.pointdir"
)


def _test_point_directory(
    point_dir_path=Path,
):

    point_dir_inst = PointDirectory(point_dir_path)

    gjf_path = point_dir_inst.gjf.path
    gaussian_out_path = point_dir_inst.gaussian_output.path
    xyz_inst = point_dir_inst.xyz.path
    ints_path = point_dir_inst.ints.path
    aim_path = point_dir_inst.aim.path
    wfn_path = point_dir_inst.wfn.path

    # check that each file/dir type can be accessed as an attribute
    # by the contents class variable
    assert gjf_path.exists() is True
    assert gaussian_out_path.exists() is True
    assert xyz_inst.exists() is True
    assert ints_path.exists() is True
    assert aim_path.exists() is True
    assert wfn_path.exists() is True

    expected_raw_data = {
        "gaussian_output": {
            "global_forces": {
                "O1": np.array([0.02953315, 0.0827204, -0.02495305]),
                "H2": np.array([0.00578961, -0.0242831, -0.00842433]),
                "H3": np.array([-0.03532276, -0.05843731, 0.03337739]),
            },
            "charge": 0,
            "multiplicity": 1,
            "molecular_dipole": MolecularDipole(x=0.1189, y=2.3866, z=0.0787),
            "molecular_quadrupole": MolecularQuadrupole(
                xx=-6.5273, yy=-7.7674, zz=-6.2577, xy=0.0665, xz=-1.6318, yz=-0.0495
            ),
            "traceless_molecular_quadrupole": TracelessMolecularQuadrupole(
                xx=0.3235, yy=-0.9166, zz=0.5931, xy=0.0665, xz=-1.6318, yz=-0.0495
            ),
            "molecular_octupole": MolecularOctupole(
                xxx=0.5348,
                yyy=8.5805,
                zzz=0.2229,
                xyy=0.1794,
                xxy=3.083,
                xxz=0.0727,
                xzz=0.1817,
                yzz=3.0764,
                yyz=0.0143,
                xyz=0.0059,
            ),
            "molecular_hexadecapole": MolecularHexadecapole(
                xxxx=-8.283,
                yyyy=-15.2596,
                zzzz=-8.1733,
                xxxy=-0.2961,
                xxxz=-0.1375,
                yyyx=-0.296,
                yyyz=0.056,
                zzzx=-0.1975,
                zzzy=0.0334,
                xxyy=-3.888,
                xxzz=-2.4818,
                yyzz=-3.8474,
                xxyz=-0.0404,
                yyxz=-0.2009,
                zzxy=-0.0859,
            ),
        },
        "wfn": {"energy": -76.421710687455, "virial_ratio": 2.01177209},
        "ints": {
            "O1": {
                "iqa": -75.446714709,
                "integration_error": -2.8725236559e-05,
                "q00": -1.051921199,
                "q10": -0.020042356378,
                "q11c": 0.0018273275449,
                "q11s": -0.20706556929,
                "q20": -0.037266216811,
                "q21c": -0.79780613831,
                "q21s": 0.013146921148,
                "q22c": -0.19595266005,
                "q22s": 0.078488472227,
                "q30": 0.043015515207,
                "q31c": -0.053621704828,
                "q31s": 0.21644282193,
                "q32c": -0.029607236961,
                "q32s": -0.89197505111,
                "q33c": -0.053969314597,
                "q33s": 0.16211677693,
                "q40": -1.4545843935,
                "q41c": 0.91783517331,
                "q41s": 0.17650015949,
                "q42c": -0.73112185714,
                "q42s": -0.3293114897,
                "q43c": 2.8344280941,
                "q43s": -0.16267842746,
                "q44c": -1.3853362266,
                "q44s": 0.089771195512,
                "q50": -0.24411738335,
                "q51c": 0.48960856702,
                "q51s": -1.5472642317,
                "q52c": -0.040094542612,
                "q52s": 0.98097072569,
                "q53c": 0.72718022845,
                "q53s": -1.1988409017,
                "q54c": -0.47766441277,
                "q54s": 2.0753064137,
                "q55c": -0.29405113415,
                "q55s": -1.6430303594,
            },
            "H2": {
                "iqa": -0.48880091691,
                "integration_error": 1.8741005824e-05,
                "q00": 0.55107276527,
                "q10": -0.10046776424,
                "q11c": 0.082404094273,
                "q11s": -0.12293368007,
                "q20": 0.0036460292977,
                "q21c": 0.00029619225829,
                "q21s": -0.0074877731368,
                "q22c": 0.0074481701736,
                "q22s": 0.0056874730269,
                "q30": -0.05956450163,
                "q31c": -0.039733101597,
                "q31s": 0.041495598451,
                "q32c": -0.028165432797,
                "q32s": -0.11949807302,
                "q33c": 0.058162645861,
                "q33s": 0.018335018802,
                "q40": -0.12002978326,
                "q41c": 0.040444633273,
                "q41s": -0.069505346729,
                "q42c": -0.019427525486,
                "q42s": -0.15727748843,
                "q43c": 0.1932877549,
                "q43s": 0.062934026281,
                "q44c": -0.057209327496,
                "q44s": 0.059969789986,
                "q50": -0.011914817313,
                "q51c": 0.062065103525,
                "q51s": -0.076563819972,
                "q52c": 0.048593580786,
                "q52s": 0.026776257085,
                "q53c": 0.072780829944,
                "q53s": 0.028736420893,
                "q54c": -0.04279361242,
                "q54s": 0.10697549721,
                "q55c": -0.031070190556,
                "q55s": -0.026095070495,
            },
            "H3": {
                "iqa": -0.48619221042,
                "integration_error": 1.7274446651e-05,
                "q00": 0.50085300856,
                "q10": 0.085197944712,
                "q11c": -0.087841616442,
                "q11s": -0.12029023455,
                "q20": 0.00023993899792,
                "q21c": -0.023661428009,
                "q21s": -0.021391961736,
                "q22c": -1.9131859436e-05,
                "q22s": 0.02151432195,
                "q30": 0.087599091989,
                "q31c": 0.031324229347,
                "q31s": 0.026427482381,
                "q32c": 0.023804975755,
                "q32s": -0.15674955727,
                "q33c": -0.088059760394,
                "q33s": 0.037288453803,
                "q40": -0.07444947707,
                "q41c": 0.05887992764,
                "q41s": 0.081114651822,
                "q42c": 0.0088380735081,
                "q42s": 0.083371237428,
                "q43c": 0.15535798009,
                "q43s": -0.069909915593,
                "q44c": -0.064026374739,
                "q44s": -0.057177316644,
                "q50": 0.0082484388953,
                "q51c": 0.099441485367,
                "q51s": 0.11360202978,
                "q52c": -0.01832368283,
                "q52s": -0.0010932889664,
                "q53c": 0.15341606275,
                "q53s": -0.10054868004,
                "q54c": -0.17440062253,
                "q54s": -0.0001046247894,
                "q55c": 0.045251112263,
                "q55s": 0.071037518757,
            },
        },
    }

    _compare_nested_dicts(expected_raw_data, point_dir_inst.raw_data) is True


def test_water_monomer_point_directory1():

    _test_point_directory(example_dir)
