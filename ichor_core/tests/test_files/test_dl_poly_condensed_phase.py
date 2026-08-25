"""Tests for writing the DL_POLY input files of a condensed phase system, i.e. a box of
many molecules whose molecular composition is worked out from the geometry itself."""

from ichor.core.atoms import Atom, Atoms
from ichor.core.files.dl_poly import (
    DlPolyConfig,
    DlPolyField,
    DlPolyMpoles,
    infer_molecular_composition,
)

# one molecule of each species, in the order their atoms are listed in the box
AMMONIA = [
    ("N", 0.0, 0.0, 0.0),
    ("H", 0.94, 0.31, 0.0),
    ("H", -0.47, 0.31, 0.81),
    ("H", -0.47, 0.31, -0.81),
]
WATER = [("O", 0.0, 0.0, 0.0), ("H", 0.76, 0.59, 0.0), ("H", -0.76, 0.59, 0.0)]

# far enough apart that the molecules of the box are not bonded to one another
MOLECULE_SPACING = 5.0


def _box(*molecules) -> Atoms:
    """Builds a box holding the given molecules, each moved onto its own site of a line so
    that they are separate molecules rather than one big one."""
    atoms = Atoms()
    for index, molecule in enumerate(molecules):
        for atom_type, x, y, z in molecule:
            atoms.add(Atom(atom_type, x + index * MOLECULE_SPACING, y, z))
    return atoms


def _config_labels(path):
    """The atom labels of a CONFIG file: the five header lines are skipped and then every
    other line is an atom line (each atom is a label line followed by a coordinate line)."""
    return [line.split()[2] for line in path.read_text().splitlines()[5::2]]


def test_infer_molecular_composition_of_one_species():
    """A box of one substance is split into its molecules and they are counted."""

    composition = infer_molecular_composition(_box(*([AMMONIA] * 5)))

    assert len(composition.species) == 1
    assert composition.species[0].nummols == 5
    assert composition.species[0].natoms == 4
    assert composition.species[0].formula == "NH3"
    assert composition.species[0].atom_names == ["N1", "H2", "H3", "H4"]
    assert composition.nmolecules == 5
    assert composition.total_atoms == 20


def test_infer_molecular_composition_of_a_mixture():
    """The molecules of a mixture are collected into a species each, in the order the
    species first appear in the box, and named in that same order."""

    composition = infer_molecular_composition(
        _box(AMMONIA, WATER, AMMONIA, WATER, WATER),
        system_names=["AMMONIA", "WATER"],
    )

    assert [species.system_name for species in composition.species] == [
        "AMMONIA",
        "WATER",
    ]
    assert [species.nummols for species in composition.species] == [2, 3]
    assert composition.total_atoms == 2 * 4 + 3 * 3


def test_config_labels_atoms_by_their_position_in_their_own_molecule(tmp_path):
    """Every molecule of a species is labelled with the same atom names, so that the one set
    of models made for the species is used for all of its copies. This is what a single
    molecule CONFIG (whose labels run over the whole geometry) cannot do."""

    box = _box(AMMONIA, AMMONIA, WATER)
    composition = infer_molecular_composition(box, ["AMMONIA", "WATER"])

    path = tmp_path / "CONFIG"
    DlPolyConfig(
        "IGNORED", [box], path=path, cell_size=20.0, composition=composition
    ).write()

    labels = _config_labels(path)
    assert labels == [
        "AMMONIA_N1",
        "AMMONIA_H2",
        "AMMONIA_H3",
        "AMMONIA_H4",
        "AMMONIA_N1",
        "AMMONIA_H2",
        "AMMONIA_H3",
        "AMMONIA_H4",
        "WATER_O1",
        "WATER_H2",
        "WATER_H3",
    ]


def test_config_groups_the_molecules_of_a_species_together(tmp_path):
    """DL_POLY reads the CONFIG atoms into the molecular types the FIELD file declares in
    order, so all the molecules of a species are written out together even when the geometry
    interleaves them."""

    box = _box(AMMONIA, WATER, AMMONIA)
    composition = infer_molecular_composition(box, ["AMMONIA", "WATER"])

    path = tmp_path / "CONFIG"
    DlPolyConfig(
        "IGNORED", [box], path=path, cell_size=20.0, composition=composition
    ).write()

    labels = _config_labels(path)
    # both ammonia molecules first, then the water, rather than the box's own order
    assert labels[:8] == ["AMMONIA_N1", "AMMONIA_H2", "AMMONIA_H3", "AMMONIA_H4"] * 2
    assert labels[8:] == ["WATER_O1", "WATER_H2", "WATER_H3"]


def test_field_declares_one_molecular_type_per_species(tmp_path):
    """Each species is declared once, with how many copies of it there are and the bonded
    terms of a *single* molecule of it (which DL_POLY applies to every copy)."""

    box = _box(AMMONIA, WATER, WATER)
    composition = infer_molecular_composition(box, ["AMMONIA", "WATER"])

    path = tmp_path / "FIELD"
    DlPolyField("IGNORED", box, path=path, composition=composition).write()
    contents = path.read_text()

    assert "Molecular types 2\n" in contents
    assert "AMMONIA\nnummols 1\natoms 4\n" in contents
    assert "WATER\nnummols 2\natoms 3\n" in contents
    # the bonded terms are those of one molecule, not of the whole box
    assert contents.count("BONDS 3\n") == 1  # ammonia: N-H, N-H, N-H
    assert contents.count("BONDS 2\n") == 1  # water: O-H, O-H
    # one "finish" per molecular type and a single "close" at the end
    assert contents.count("finish\n") == 2
    assert contents.endswith("close\n")


def test_field_all_pairs_bonds_stay_within_one_molecule(tmp_path):
    """For a multipole run every intramolecular pair is excluded from the electrostatics.
    The exclusions belong to the single molecule the type is declared from, so they must not
    grow with how many copies of it the box holds."""

    composition = infer_molecular_composition(_box(*([WATER] * 4)), ["WATER"])

    path = tmp_path / "FIELD"
    DlPolyField(
        "IGNORED",
        Atoms(),
        path=path,
        multipolar=2,
        all_pairs_bonds=True,
        composition=composition,
    ).write()
    contents = path.read_text()

    assert "Multipolar 2\n" in contents
    # the three pairs of a single water molecule, not of all four of them
    assert "BONDS 3\n" in contents
    assert "ANGLES" not in contents


def test_mpoles_mirrors_the_molecular_types_of_the_field_file(tmp_path):
    """DL_POLY matches the MPOLES file up against the FIELD file, so it declares the same
    molecules with the same counts."""

    box = _box(AMMONIA, WATER, WATER)
    composition = infer_molecular_composition(box, ["AMMONIA", "WATER"])

    path = tmp_path / "MPOLES"
    DlPolyMpoles("IGNORED", box, path=path, composition=composition).write()
    contents = path.read_text()

    assert "MOLECULES 2\n" in contents
    assert "AMMONIA\nNUMMOLS 1\nATOMS 4\n" in contents
    assert "WATER\nNUMMOLS 2\nATOMS 3\n" in contents
    assert contents.count("FINISH\n") == 2
    assert contents.endswith("CLOSE\n")


def test_single_molecule_files_are_unaffected_by_the_composition_support(tmp_path):
    """Without a composition the files are written exactly as they were before it existed:
    one molecular type, and CONFIG labels running over the whole geometry."""

    atoms = _box(AMMONIA)

    config_path = tmp_path / "CONFIG"
    DlPolyConfig("AMMONIA", [atoms], path=config_path, cell_size=25.0).write()
    labels = _config_labels(config_path)
    assert labels == ["AMMONIA_N1", "AMMONIA_H2", "AMMONIA_H3", "AMMONIA_H4"]

    field_path = tmp_path / "FIELD"
    DlPolyField("AMMONIA", atoms, path=field_path).write()
    field = field_path.read_text()
    assert "Molecular types 1\n" in field
    assert "AMMONIA\nnummols 1\natoms 4\n" in field
