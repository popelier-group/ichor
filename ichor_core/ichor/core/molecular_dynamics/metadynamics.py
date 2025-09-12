from pathlib import Path

from ase import io

from rdkit import Chem
from rdkit.Chem import inchi, AllChem, Draw
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem import rdDetermineBonds
from rdkit.Chem import rdMolDescriptors

# Define SMARTS patterns for common functional groups
functional_groups = {
    "alkene": "C=C",
    "alkyne": "C#C",
    "carboxylic_acid": "[CX3](=O)[OX2H1]",  # COOH
    "alcohol": "[OX2H][CX4]",  # OH on sp3 carbon
    "amine_primary": "[NX3;H2][CX4]",  # NH2
    "ketone": "[CX3](=O)[CX4]",  # RC(=O)R'
    "aldehyde": "[CX3H1](=O)[#6]",  # R-CHO
    "ester": "[CX3](=O)[OX2][CX3]",  # RCOOR'
    "ether": "[OD2]([#6])[#6]",  # R-O-R'
    "amide": "[NX3][CX3](=O)[#6]",  # RCONR2
    "halide": "[F,Cl,Br,I]",  # Halogens
    "epoxide": "C1OC1",  # Epoxide
    "Imine": "C=N",  # Imine
    "Nitrile": "C#N",  # Nitrile
    "Nitro": "[NX3](=O)[O-]",  # Nitro
    "Azide": "[N-]=[N+]=N",  # Azide
    "Diazonium": "[N+](=N)[O-]",  # Diazonium
    "Thiol": "[SX2H]",  # Thiol
    "Thioether": "[SX2][#6]",  # Thioether
    "Sulfoxide": "S(=O)[#6]",  # Sulfoxide
    "Sulfone": "S(=O)(=O)[#6]",  # Sulfone
    "Sulfonic acid": "S(=O)(=O)[OH]",  # Sulfonic Acid
    "Phosphate ester": "P(=O)(O)(O)[#6]",  # Phosphate Ester
    "Phosphine oxide": "P(=O)(C)(C)",  # Phosphine Oxide
    "Isocyanate": "N=C=O",  # Isocyanate
    "Isothiocyanate": "N=C=S",  # Isothiocyanate
}


class Metadynamics_In:

    xyz_path = "[data from file]"
    collective_variables = "[]"
    timestep = "float"
    num_timesteps = "int"
    time_units = "str"
    dist_units = "str"
    energy_units = "str"
    height = "[]"
    pace = "[]"
    sigma = "[]"
    grid_min = "[-pi]"
    grid_max = "[pi]"
    grid_bin = "[150]"
    bias_factor = "[]"
    file = "[HILLS...]"
    temperature = "float"


def convert_xyz_to_mol(xyz_file):
    xyz_path = Path(xyz_file)
    if xyz_path.exists() and xyz_path.is_file() and xyz_path.suffix == ".xyz":
        # ensure only xyz columns present
        loaded_atoms = io.read(xyz_path)
        io.write(
            filename=str(xyz_path),
            images=loaded_atoms,
            format="xyz",
        )
        # convert to mol
        mol = Chem.rdmolfiles.MolFromXYZFile(str(xyz_path))
        loaded_mol = Chem.Mol(mol)
        rdDetermineBonds.DetermineBonds(loaded_mol)
        print("LOADING MOLECULE INTO RDKIT")
        return loaded_mol
    else:
        print("NO XYZ FILE LOADED")


def print_molecule_information(mol):
    print("\nMOLECULE DESCRIPTORS:\n")
    ## molecule descriptors
    # smiles
    smiles = Chem.MolToSmiles(mol, canonical=True)
    print("SMILES:", smiles)
    # inchi strings
    inchi_str = inchi.MolToInchi(mol)
    inchi_key = inchi.InchiToInchiKey(inchi_str)
    print("InChI:", inchi_str)
    print("InChIKey:", inchi_key)


def print_neighbour_information(mol):
    print("\nNEIGHBOUR INFORMATION:\n")
    # sanitise and add hydrogens
    mol = Chem.AddHs(mol)

    ## list atoms and their neighbours
    print("Neighbour list: ")
    for atom in mol.GetAtoms():
        idx = atom.GetIdx()
        symbol = atom.GetSymbol()
        neighbors = atom.GetNeighbors()
        neighbor_labels = [f"{nbr.GetSymbol()}{nbr.GetIdx()}" for nbr in neighbors]
        print(f"{symbol}{idx} --> {', '.join(neighbor_labels)}")


def print_ring_information(mol):
    print("\nRING INFORMATION:\n")
    # Get all rings (as tuples of atom indices)
    ring_info = mol.GetRingInfo()
    atom_rings = ring_info.AtomRings()
    # Filter for aromatic rings
    aromatic_rings = []
    for ring in atom_rings:
        if all(mol.GetAtomWithIdx(idx).GetIsAromatic() for idx in ring):
            aromatic_rings.append(ring)

    print("All rings in molecule: ", atom_rings)
    print("All aromatic rings in molecule: ", aromatic_rings)


def print_functional_groups(mol):
    print("\nFUNCTIONAL GROUP INFORMATION:\n")
    groups = {}
    for name, smarts in functional_groups.items():
        patt = Chem.MolFromSmarts(smarts)
        matches = mol.GetSubstructMatches(patt)
        labeled_matches = []
        for match in matches:
            labeled = [f"{mol.GetAtomWithIdx(idx).GetSymbol()}{idx}" for idx in match]
            labeled_matches.append(labeled)
        if labeled_matches:
            groups[name] = labeled_matches

    # Print results
    for group, matches in groups.items():
        print(f"{group}:")
        for atoms in matches:
            print("  " + ", ".join(atoms))


def print_rotatable_bonds(mol):
    print("\nROTATABLE BOND INFORMATION:\n")
    rotatable_bonds = []
    for bond in mol.GetBonds():
        # Criteria: single bond, not in ring, between non-terminal heavy atoms
        if bond.GetBondType() == Chem.rdchem.BondType.SINGLE and not bond.IsInRing():
            a1 = bond.GetBeginAtom()
            a2 = bond.GetEndAtom()
            if a1.GetDegree() > 1 and a2.GetDegree() > 1:
                rotatable_bonds.append((a1.GetIdx(), a2.GetIdx()))

    print(f"Number of rotatable bonds: {len(rotatable_bonds)}")
    for i, (a1, a2) in enumerate(rotatable_bonds):
        print(f"Rotatable bond {i+1}: atoms {a1} - {a2}")


def print_dihedrals(mol):
    print("\nROTATABLE DIHEDRAL INFORMATION:\n")
    dihedrals = []
    for bond in mol.GetBonds():
        if bond.GetBondType() != Chem.rdchem.BondType.SINGLE or bond.IsInRing():
            continue
        a1 = bond.GetBeginAtom()
        a2 = bond.GetEndAtom()
        if a1.GetDegree() <= 1 or a2.GetDegree() <= 1:
            continue
        # Find neighbor of a1 that's not a2
        a0 = next(
            (
                nbr
                for nbr in a1.GetNeighbors()
                if nbr.GetIdx() != a2.GetIdx() and nbr.GetAtomicNum() > 1
            ),
            None,
        )
        # Find neighbor of a2 that's not a1
        a3 = next(
            (
                nbr
                for nbr in a2.GetNeighbors()
                if nbr.GetIdx() != a1.GetIdx() and nbr.GetAtomicNum() > 1
            ),
            None,
        )
        if a0 and a3:
            dihedrals.append((a0.GetIdx(), a1.GetIdx(), a2.GetIdx(), a3.GetIdx()))

    print(f"Number of rotatable dihedrals: {len(dihedrals)}")
    for i, (a0, a1, a2, a3) in enumerate(dihedrals):
        print(f"Dihedral {i+1}: atoms {a0} - {a1} - {a2} - {a3}")


def print_hbond_info(mol):
    print("\nHYDROGEN BOND INFORMATION:\n")
    donors = rdMolDescriptors.CalcNumHBD(mol)
    acceptors = rdMolDescriptors.CalcNumHBA(mol)

    print(f"H-bond donors: {donors}")
    print(f"H-bond acceptors: {acceptors}")
    # Donor: [!H0;#7,#8] — N or O with at least one hydrogen
    donor_smarts = Chem.MolFromSmarts("[!H0;#7,#8]")
    donor_matches = mol.GetSubstructMatches(donor_smarts)

    # Acceptor: [#8,#7] — O or N atoms
    acceptor_smarts = Chem.MolFromSmarts("[#8,#7]")
    acceptor_matches = mol.GetSubstructMatches(acceptor_smarts)

    print("Donor atom indices:", donor_matches)
    print("Acceptor atom indices:", acceptor_matches)


def draw_labeled_molecule(mol_path):

    mol = convert_xyz_to_mol(mol_path)
    xyz_path = Path(mol_path)

    AllChem.Compute2DCoords(mol)
    mol = rdMolDraw2D.PrepareMolForDrawing(mol)

    atom_labels = {
        atom.GetIdx(): f"{atom.GetSymbol()}{atom.GetIdx()}" for atom in mol.GetAtoms()
    }

    drawer = rdMolDraw2D.MolDraw2DCairo(500, 400)
    opts = drawer.drawOptions()
    for idx, label in atom_labels.items():
        opts.atomLabels[idx] = label

    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()

    filename = xyz_path.with_suffix(".png")

    with open(filename, "wb") as f:
        f.write(drawer.GetDrawingText())
    print(f"Image saved to {filename}")


def print_molecule_data(mol_path):
    mol = convert_xyz_to_mol(mol_path)
    print_molecule_information(mol)
    print_neighbour_information(mol)
    print_ring_information(mol)
    print_functional_groups(mol)
    print_rotatable_bonds(mol)
    print_hbond_info(mol)
    print_dihedrals(mol)
