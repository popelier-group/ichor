import numpy as np
from ichor.core.atoms import ALF, Atom, Atoms
from ichor.core.calculators import calculate_alf_features


def test_alf_features_calculator():

    alf = [
        ALF(0, 1, 2),
        ALF(1, 0, 2),
        ALF(2, 0, 1),
        ALF(3, 2, 4),
        ALF(4, 3, 5),
        ALF(5, 4, 3),
    ]

    # make up some geometry to test features
    atoms = Atoms(
        [
            Atom("O", -2.1180124028, 2.6912012640, 0.0151569307),
            Atom("H", -1.1501254774, 2.7214377667, -0.0200801898),
            Atom("H", -2.3968615982, 3.2955257987, -0.6891128927),
            Atom("O", -10.1180124028, 10.6912012640, 10.0151569307),
            Atom("H", -10.1501254774, 10.7214377667, -10.0200801898),
            Atom("H", -10.3968615982, 10.2955257987, -10.6891128927),
        ]
    )

    true_features = np.array(
        [
            [
                1.83114462,
                1.83114462,
                1.81475846,
                28.53423874,
                0.58566099,
                -2.90043625,
                28.64076313,
                1.59988594,
                2.08168023,
                29.33318136,
                1.64816306,
                2.08730584,
            ],
            [
                1.83114462,
                2.88549038,
                0.6634171,
                29.5575222,
                2.5056234,
                -0.21624345,
                29.57889251,
                1.54262958,
                1.0058623,
                30.27676224,
                1.49584534,
                1.00152382,
            ],
            [
                1.83114462,
                2.88549038,
                0.6634171,
                28.59009976,
                0.58860019,
                -1.45798393,
                26.87960018,
                1.60179249,
                -2.85669267,
                27.57964481,
                1.6530929,
                -2.85111109,
            ],
            [
                28.59009976,
                37.86120275,
                0.78701153,
                28.53423874,
                1.58692719,
                -0.06203155,
                29.5575222,
                1.54216462,
                -0.08907283,
                39.13609139,
                1.59389072,
                0.78131743,
            ],
            [
                37.86120275,
                1.569593,
                2.50678955,
                28.64076313,
                0.7638496,
                0.2851489,
                29.57889251,
                0.71984012,
                0.23872457,
                26.87960018,
                0.75039364,
                0.26758612,
            ],
            [
                1.569593,
                39.13609139,
                0.61101723,
                29.33318136,
                0.78818797,
                0.85987951,
                30.27676224,
                0.74574909,
                0.81492326,
                27.57964481,
                0.77723542,
                0.83865892,
            ],
        ]
    )

    features_array = atoms.features(calculate_alf_features, alf)

    # check all the individual atoms
    for i, atm in enumerate(atoms):
        atm_features = atm.features(calculate_alf_features, alf)
        np.testing.assert_allclose(atm_features, true_features[i])
        assert atm_features.shape == (12,)

    # should contain the features for all atoms, atoms x nfeatures
    assert features_array.shape == (6, 12)
    np.testing.assert_allclose(features_array, true_features)
