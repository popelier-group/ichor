
def write_control(path: Path, temperature: float = 0.0):
    with open(path / "CONTROL", "w+") as f:
        f.write(f"Title: {GLOBALS.SYSTEM_NAME}\n")
        f.write("\n")
        f.write(f"ensemble nvt hoover {GLOBALS.DLPOLY_HOOVER}\n")
        f.write("\n")
        if int(temperature) == 0:
            f.write("temperature 0\n")
            f.write("\n")
            f.write("#perform zero temperature run (really set to 10K)\n")
            f.write("zero\n")
            f.write("\n")
        else:
            f.write(f"temperature {temperature}\n")
            f.write("\n")
        f.write("\n")
        f.write(f"timestep {GLOBALS.DLPOLY_TIMESTEP}\n")
        f.write(f"steps {GLOBALS.DLPOLY_NUMBER_OF_STEPS}\n")
        f.write("scale 100\n")
        f.write("\n")
        f.write("cutoff  8.0\n")
        f.write("rvdw    8.0\n")
        f.write("vdw direct\n")
        f.write("vdw shift\n")
        f.write("fflux cluster L1\n")
        f.write("\n")
        f.write("dump  1000\n")
        f.write("traj 0 1 0\n")
        f.write("print every 1\n")
        f.write("stats every 1\n")
        f.write("fflux print 0 1\n")
        f.write("job time 10000000\n")
        f.write("close time 20000\n")
        f.write("finish\n")


def write_config(path: Path, atoms: Atoms):
    atoms.centre()

    with open(path / "CONFIG", "w+") as f:
        f.write("Frame :         1\n")
        f.write("\t0\t1\n")  # PBC Solution to temporary problem
        f.write(f"{GLOBALS.DLPOLY_CELL_SIZE} 0.0 0.0\n")
        f.write(f"0.0 {GLOBALS.DLPOLY_CELL_SIZE} 0.0\n")
        f.write(f"0.0 0.0 {GLOBALS.DLPOLY_CELL_SIZE}\n")
        for atom in atoms:
            f.write(
                f"{atom.type}  {atom.index}  {GLOBALS.SYSTEM_NAME}_{atom.type}{atom.index}\n"
            )
            f.write(f"{atom.x}\t\t{atom.y}\t\t{atom.z}\n")


def write_field(path: Path, atoms: Atoms):
    bonds, angles, dihedrals = get_internal_feature_indices(atoms)

    with open(path / "FIELD", "w") as f:
        f.write("DL_FIELD v3.00\n")
        f.write("Units kJ/mol\n")
        f.write("Molecular types 1\n")
        f.write(f"{GLOBALS.SYSTEM_NAME}\n")
        f.write("nummols 1\n")
        f.write(f"atoms {len(atoms)}\n")
        for atom in atoms:
            f.write(
                #  Atom Type      Atomic Mass                    Charge Repeats Frozen(0=NotFrozen)
                f"{atom.type}\t\t{dlpoly_weights[atom.type]:.7f}     0.0   1   0\n"
            )
        f.write(f"BONDS {len(bonds)}\n")
        for i, j in bonds:
            f.write(f"harm {i} {j} 0.0 0.0\n")
        if len(angles) > 0:
            f.write(f"ANGLES {len(angles)}\n")
            for i, j, k in angles:
                f.write(f"harm {i} {j} {k} 0.0 0.0\n")
        if len(dihedrals) > 0:
            f.write(f"DIHEDRALS {len(dihedrals)}\n")
            for i, j, k, l in dihedrals:
                f.write(f"harm {i} {j} {k} {l} 0.0 0.0\n")
        f.write("finish\n")
        f.write("close\n")


def link_models(path: Path, models: Models):
    model_dir = path / "model_krig"
    mkdir(model_dir)
    for model in models:
        ln(model.path.absolute(), model_dir)


def setup_dlpoly_directory(
    path: Path, atoms: Atoms, models: Models, temperature: float = 0.0
):
    mkdir(path)
    write_control(path, temperature=temperature)
    write_config(path, atoms)
    write_field(path, atoms)
    link_models(path, models)


def get_dlpoly_directories(models: List[Models]) -> List[Path]:
    dlpoly_directories = []
    for model in models:
        dlpoly_directories.append(
            FILE_STRUCTURE["dlpoly"]
            / f"{model.system}{str(model.ntrain).zfill(4)}"
        )
    return dlpoly_directories


@convert_to_path
def setup_dlpoly_directories(
    atoms: Atoms, models: List[Models], temperature: float = 0.0
) -> List[Path]:
    dlpoly_directories = get_dlpoly_directories(models)
    for dlpoly_dir, model in zip(dlpoly_directories, models):
        setup_dlpoly_directory(
            dlpoly_dir, atoms, model, temperature=temperature
        )
    return dlpoly_directories
