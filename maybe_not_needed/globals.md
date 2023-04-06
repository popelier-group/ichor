| Name | Type | Default Value | Notes |
| --- | --- | --- | --- |
| ACTIVE_LEARNING_METHOD | <class 'str'> | epe | Active learning method to use |
| ADD_DISPERSION_TO_IQA | <class 'bool'> | True |  |
| AIMALL_ATIDSPROPS | <class 'str'> | 0.001 |  |
| AIMALL_ATLAPRHOCPS | <class 'bool'> | False |  |
| AIMALL_AUTONNACPS | <class 'bool'> | True |  |
| AIMALL_BIM | <class 'str'> | auto |  |
| AIMALL_BOAQ | <class 'str'> | gs20 | Boaq setting used for AIMAll |
| AIMALL_CAPTURE | <class 'str'> | auto |  |
| AIMALL_CPCONN | <class 'str'> | moderate |  |
| AIMALL_DELMOG | <class 'bool'> | True |  |
| AIMALL_EHREN | <class 'int'> | 0 |  |
| AIMALL_ENCOMP | <class 'int'> | 3 | Encomp setting to use for AIMAll |
| AIMALL_F2W | <class 'str'> | wfx |  |
| AIMALL_F2WONLY | <class 'bool'> | False |  |
| AIMALL_FEYNMAN | <class 'bool'> | False |  |
| AIMALL_IASMESH | <class 'str'> | fine | Iasmesh setting used for AIMAll |
| AIMALL_IASPROPS | <class 'bool'> | True |  |
| AIMALL_IASWRITE | <class 'bool'> | False |  |
| AIMALL_INTVEEAA | <class 'str'> | new |  |
| AIMALL_MAGPROPS | <class 'str'> | none |  |
| AIMALL_MAXMEM | <class 'int'> | 2400 |  |
| AIMALL_MIR | <class 'float'> | -1.0 |  |
| AIMALL_NCORES | <class 'int'> | 2 | Number of cores to run AIMAll |
| AIMALL_N_TRIES | <class 'int'> | 10 | Number of tries to run AIMAll job before giving up, currently not used |
| AIMALL_SAW | <class 'bool'> | False |  |
| AIMALL_SCP | <class 'str'> | some |  |
| AIMALL_SHM | <class 'int'> | 5 |  |
| AIMALL_SKIPINT | <class 'bool'> | False |  |
| AIMALL_SOURCE | <class 'bool'> | False |  |
| AIMALL_VERIFYW | <class 'str'> | yes |  |
| AIMALL_WARN | <class 'bool'> | True |  |
| AIMALL_WSP | <class 'bool'> | True |  |
| AMBER_LN_GAMMA | <class 'float'> | 0.7 |  |
| AMBER_NCORES | <class 'int'> | 1 | Number of cores to run AMBER |
| AMBER_STEPS | <class 'int'> | 100000 |  |
| AMBER_TEMPERATURE | <class 'float'> | 300 | K |
| AMBER_TIMESTEP | <class 'float'> | 0.001 | ps |
| BASIS_SET | <class 'str'> | 6-31+g(d,p) | Basis set to use in quantum calculations |
| BATCH_SIZE | <class 'int'> | 5000 | Some calculations will split up sample set calculations into batches to save memory |
| CP2K_BASIS_SET | <class 'str'> | 6-31G* |  |
| CP2K_DATA_DIR | <class 'str'> |  |  |
| CP2K_INPUT | <class 'str'> |  |  |
| CP2K_METHOD | <class 'str'> | BLYP |  |
| CP2K_NCORES | <class 'int'> | 8 | Number of cores to run CP2K |
| CP2K_STEPS | <class 'int'> | 10000 |  |
| CP2K_TEMPERATURE | <class 'int'> | 300 | K |
| CP2K_TIMESTEP | <class 'float'> | 1.0 | fs |
| DISABLE_PROBLEMS | <class 'bool'> | False |  |
| DLPOLY_CELL_SIZE | <class 'float'> | 25.0 | Cell size for DLPOLY simulation |
| DLPOLY_CHECK_CONVERGENCE | <class 'bool'> | False | Flag to check for convergence in DLPOLY geometry optimisations |
| DLPOLY_CONVERGENCE_CRITERIA | <class 'int'> | -1 | table-optkingconv (criteria number is index of table row starting at 1, <= 0 criteria must be defined explicitly) |
| DLPOLY_HOOVER | <class 'float'> | 0.04 | Parameter for timecon parameter of Nose-Hoover thermostat in DLPOLY |
| DLPOLY_LOCATION | <class 'pathlib.Path'> | None | Path to custom DLPOLY executable |
| DLPOLY_MAX_DISP | <class 'float'> | -1.0 |  |
| DLPOLY_MAX_ENERGY | <class 'float'> | -1.0 |  |
| DLPOLY_MAX_FORCE | <class 'float'> | -1.0 |  |
| DLPOLY_NCORES | <class 'int'> | 1 | Number of cores to run DLPOLY |
| DLPOLY_NUMBER_OF_STEPS | <class 'int'> | 500 | Number of steps to run simulation for |
| DLPOLY_PRINT_EVERY | <class 'int'> | 1 | DLPOLY output prints every `DLPOLY_PRINT_EVERY` timesteps |
| DLPOLY_RMS_DISP | <class 'float'> | -1.0 |  |
| DLPOLY_RMS_FORCE | <class 'float'> | -1.0 |  |
| DLPOLY_TEMPERATURE | <class 'int'> | 0 | Temperature to run DLPOLY simulation (K) |
| DLPOLY_TIMESTEP | <class 'float'> | 0.001 | Length of timestep in DLPOLY simulation (ps) |
| DLPOLY_VERSION | <class 'ichor.core.common.types.version.Version'> | 4.9.0 | Current DLPOLY version, no longer support < 4.09 |
| DROP_COMPUTE | <class 'bool'> | False |  |
| DROP_COMPUTE_LOCATION | <class 'pathlib.Path'> |  |  |
| DROP_COMPUTE_NTRIES | <class 'int'> | 1000 |  |
| EXCLUDE_NODES | typing.List[str] | [] |  |
| FEREBUS_COGNITIVE_LEARNING_RATE | <class 'float'> | 1.494 | Cognitive learning rate for FEREBUS PSO |
| FEREBUS_CONVERGENCE | <class 'int'> | 20 | Old version of FEREBUS_STALL_ITERATIONS, not currently used |
| FEREBUS_INERTIA_WEIGHT | <class 'float'> | 0.729 | Inertia weight for FEREBUS PSO |
| FEREBUS_LIKELIHOOD | <class 'str'> | concentrated | Likelihood function to use in ferebus |
| FEREBUS_LOCATION | <class 'pathlib.Path'> | None | Path to custom ferebus executable |
| FEREBUS_MAX_ITERATION | <class 'int'> | 1000 | Number of iterations FEREBUS PSO should run for |
| FEREBUS_MEAN | <class 'str'> | constant | Mean function for ferebus to use |
| FEREBUS_NCORES | <class 'int'> | 4 | Number of cores to run FEREBUS |
| FEREBUS_NUGGET | <class 'float'> | 1e-10 | Nugget parameter for FEREBUS |
| FEREBUS_OPTIMISATION | <class 'str'> | pso | Optimiser for ferebus |
| FEREBUS_SOCIAL_LEARNING_RATE | <class 'float'> | 1.494 | Social learning rate for FEREBUS PSO |
| FEREBUS_STALL_ITERATIONS | <class 'int'> | 20 | Stall iterations for relative difference calculation in ferebus PSO |
| FEREBUS_SWARM_SIZE | <class 'int'> | 50 | Swarm size for FEREBUS PSO |
| FEREBUS_THETA_MAX | <class 'float'> | 3.0 | Max theta value for PSO initialisation in FEREBUS |
| FEREBUS_THETA_MIN | <class 'float'> | 0.0 | Min theta value for PSO initialisation in FEREBUS |
| FEREBUS_TOLERANCE | <class 'float'> | 1e-08 | Tolerance for relative difference calculation in ferebus PSO |
| FEREBUS_TYPE | <class 'str'> | executable | Tells ichor to run FEREBUS or FEREBUS.py |
| FEREBUS_VERSION | <class 'ichor.core.common.types.version.Version'> | 7.0.0 | Current ferebus version, currently does nothing |
| GAUSSIAN_MEMORY_LIMIT | <class 'str'> | 1GB | Memory limit for runnning Gaussian |
| GAUSSIAN_NCORES | <class 'int'> | 2 | Number of cores to run Gaussian |
| GAUSSIAN_N_TRIES | <class 'int'> | 10 | Number of tries to run Gaussian job before giving up, currently not used |
| GIT_PASSWORD | <class 'str'> |  |  |
| GIT_TOKEN | <class 'str'> |  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 |  |
| GIT_USERNAME | <class 'str'> |  |  |
| INCLUDE_NODES | typing.List[str] | [] |  |
| INTEGRATION_ERROR_THRESHOLD | <class 'float'> | 0.001 |  |
| KERNEL | <class 'str'> | periodic | Kernel to use in ferebus |
| KEYWORDS | typing.List[str] | ['nosymm'] | Keywords used to run Gaussian |
| LOG_WARNINGS | <class 'bool'> | False |  |
| MAX_NUGGET | <class 'float'> | 0.0001 | ICHOR v2 iteratively increased nugget value when near singular matrix was encountered, not currently used |
| MAX_RUNNING_TASKS | <class 'int'> | -1 | Number of concurrent tasks to run in queueing system, set to <= 0 for unlimited tasks |
| METHOD | <class 'str'> | B3LYP | Active learning method to use |
| MORFI_ANGULAR | <class 'int'> | 5 |  |
| MORFI_ANGULAR_H | <class 'int'> | 5 |  |
| MORFI_NCORES | <class 'int'> | 4 | Number of cores to run Morfi |
| MORFI_RADIAL | <class 'float'> | 10.0 |  |
| MORFI_RADIAL_H | <class 'float'> | 8.0 |  |
| NORMALISE | <class 'bool'> | False | Whether to normalise data before running through ferebus, currently not used |
| N_ITERATIONS | <class 'int'> | 1 | Number of iterations to run adaptive sampling for |
| OPTIMISE_ATOM | <class 'str'> | all | Atom to optimise in adaptive sampling |
| OPTIMISE_PROPERTY | <class 'str'> | iqa | Atomic property to optimise in adaptive sampling |
| OPTIMUM_ENERGY | <class 'float'> | None |  |
| OPTIMUM_ENERGY_FILE | <class 'pathlib.Path'> | None |  |
| PANDORA_CCSDMOD | <class 'str'> | ccsdM |  |
| PANDORA_LOCATION | <class 'pathlib.Path'> |  |  |
| POINTS_PER_ITERATION | <class 'int'> | 1 | Number of points to add to training set per iteration |
| PYSCF_NCORES | <class 'int'> | 2 | Number of cores to run PySCF |
| RECOVERY_ERROR_THRESHOLD | <class 'float'> | 0.00038087988471333236 |  |
| RERUN_POINTS | <class 'bool'> | False |  |
| SAMPLE_POINTS | <class 'int'> | 9000 | Number of sample points to initialise sample pool with |
| SAMPLE_POOL_METHOD | typing.List[str] | ['random'] | Methods to initialise sample pool |
| SCRUB_POINTS | <class 'bool'> | True | Whether to use points scrubbing |
| STANDARDISE | <class 'bool'> | False | Whether to standardise data before running through ferebus, currently not used |
| SYSTEM_NAME | <class 'str'> | SYSTEM | Name of the current system |
| TRAINING_POINTS | <class 'int'> | 500 | Number of training points to initialise training set with |
| TRAINING_SET_METHOD | typing.List[str] | ['min_max_mean'] | Methods to initialise training set |
| TYCHE_LOCATION | <class 'pathlib.Path'> | None |  |
| TYCHE_NCORES | <class 'int'> | 1 | Number of cores to run TYCHE |
| TYCHE_STEPS | <class 'int'> | 10000 |  |
| TYCHE_TEMPERATURE | <class 'float'> | 300 | K |
| VALIDATION_POINTS | <class 'int'> | 500 | Number of validation points to initialise validation set with |
| VALIDATION_SET_METHOD | typing.List[str] | ['random'] | Methods to initialise validation set |
| WARN_INTEGRATION_ERROR | <class 'bool'> | True |  |
| WARN_RECOVERY_ERROR | <class 'bool'> | True |  |
