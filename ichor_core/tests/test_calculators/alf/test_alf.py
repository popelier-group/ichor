from ichor.core.atoms import ALF, Atom, Atoms
from ichor.core.calculators import (
    calculate_alf_atom_sequence,
    calculate_alf_cahn_ingold_prelog,
)


def test_water():
    water = Atoms(
        [
            Atom("O", -2.1180124028, 2.6912012640, 0.0151569307),
            Atom("H", -1.1501254774, 2.7214377667, -0.0200801898),
            Atom("H", -2.3968615982, 3.2955257987, -0.6891128927),
        ]
    )

    cahn_ingold_prelog_alf = [
        ALF(0, 1, 2),
        ALF(1, 0, 2),
        ALF(2, 0, 1),
    ]

    sequence_alf = [
        ALF(0, 1, 2),
        ALF(1, 0, 2),
        ALF(2, 1, 3),
        ALF(3, 2, 4),
        ALF(4, 3, 5),
        ALF(5, 3, 4),
    ]

    # geometry to test sequence calculator
    # coordinates of the atoms do not matter
    water_dimer_sequence = Atoms(
        [
            Atom("O", -2.1180124028, 2.6912012640, 0.0151569307),
            Atom("H", -1.1501254774, 2.7214377667, -0.0200801898),
            Atom("H", -2.3968615982, 3.2955257987, -0.6891128927),
            Atom("O", -10.1180124028, 10.6912012640, 10.0151569307),
            Atom("H", -10.1501254774, 10.7214377667, -10.0200801898),
            Atom("H", -10.3968615982, 10.2955257987, -10.6891128927),
        ]
    )

    for atom in water:
        assert calculate_alf_cahn_ingold_prelog(atom) == cahn_ingold_prelog_alf[atom.i]

    for atom in water_dimer_sequence:
        assert calculate_alf_atom_sequence(atom) == sequence_alf[atom.i]
