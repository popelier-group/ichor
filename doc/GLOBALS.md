# Globals
List of global variables that can be set in the config file with the exception of `DEFAULT_CONFIG_FILE`

`DEFAULT_CONFIG_FILE` can be set when running ICHOR with the `-c` flag, e.g.
```
python ICHOR.py -c config.properties
```
Currently supported filetypes are:
* .properties
* .yaml

All other global variables can be set in this config file

|Variable Name|Description|Default Value|Allowed Values|
|-------------|-----------|-------------|--------------|
|DEFAULT_CONFIG_FILE|Config file location for ICHOR|config.properties|Config File String|
|SYSTEM_NAME|Name of the system you're working on (e.g. WATER)|SYSTEM|Any String|
|ALF|Nx3 Matrix of the ALF of your system|[ ] (set automatically)|List of Lists e.g. [[1,2,3],[2,1,3],[3,1,2]]|
|ALF_REFERENCE_FILE|Sets file for ICHOR to calculate ALF from|Set to the first Training Point if available|Any GJF file|
|MAX_ITERATION|Number of iterations the adaptive sampling will run for|1|Integer >= 1|
|POINTS_PER_ITERATION|Number of points added per iteration|1|Integer >= 1|
|METHOD|Quantum chemistry method used by Gaussian|B3LYP|Any Method Implemented in G09|
|BASIS_SET|Quantum chemistry basis set used by Gaussian|6-31+g(d,p)|Any Basis Set Implemented in G09|
|Keywords|List of Keywords that will be used in Gaussian|[ ]|List of keywords inputted as a string separated by spaces e.g.("nosymm 6d 10f")|
|Encomp|Encomp keyword used by AIMAll (3 -> A,A', 4 -> A,A' + A,B)|3|3 OR 4|
|BOAQ|BOAQ keyword used by AIMAll|gs20|BOAQ allowed values can be found in _BOAQ_VALUES|
|IASMESH|IASMESH keyword used by AIMAll|fine|IASMESH allowed values can be found in _IASMESH_VALUES|
|KERNEL|Kernel to be used by GPR Method (Currently does nothing)|rbf|Not Implemented|
|FEREBUS_VERSION|Switch between using either FEREBUS.py or FEREBUS|python|fortran OR python|
|FEREBUS_LOCATION|Sets location of FEREBUS program|PROGRAMS/FEREBUS|Any path to FEREBUS|
|GAUSSIAN_CORE_COUNT|Core count for Gaussian|2|Integer >= 1|
|AIMAll_CORE_COUNT|Core count for AIMAll|2|Integer >= 1|
|FEREBUS_CORE_COUNT|Core count for FEREBUS|4|Integer >= 1|
|DLPOLY_CORE_COUNT|Core count for DLPOLY|1|Integer >= 1|
|DLPOLY_NUMBER_OF_STEPS|Number of steps to run DLPOLY for|500|Integer >= 1|
|DLPOLY_TEMPERATURE|Temperature to run DLPOLY at (0 K will perform Geom. Opt.)|0|Float >= 0|
|DLPOLY_PRINT_EVERY|Frequency DLPOLY prints statistics for|1|Integer >= 1|
|DLPOLY_TIMESTEP|Timestep in ps DLPOLY will run at|0.001|Float > 0|
|DLPOLY_LOCATION|Sets location of DLPOLY program|PROGRAMS/DLPOLY.Z|Any path to DLPOLY|
|DLPOLY_CHECK_CONVERGENCE|Tells DLPOLY to use convergence criteria during optimisation|False|True OR False|
|DLPOLY_CONVERGENCE_CRITERIA|Sets Pre-Set DLPOLY convergence criteria|-1 (Uses DLPOLY Default)|Integer Between 1-10|
|DLPOLY_MAX_ENERGY|Sets DLPOLY Max Energy Convergence Threshold|-1 (Uses DLPOLY Default)|Float > 0|
|DLPOLY_MAX_FORCE|Sets DLPOLY Max Force Convergence Threshold|-1 (Uses DLPOLY Default)|Float > 0|
|DLPOLY_RMS_FORCE|Sets DLPOLY RMS Force Convergence Threshold|-1 (Uses DLPOLY Default)|Float > 0|
|DLPOLY_MAX_DISP|Sets DLPOLY Max Displacement Convergence Threshold|-1 (Uses DLPOLY Default)|Float > 0|
|DLPOLY_RMS_DISP|Sets DLPOLY RMS Displacement Convergence Threshold|-1 (Uses DLPOLY Default)|Float > 0|
|MACHINE|Used to identify which machine ICHOR is running on|(set automatically)|local OR csf2 OR csf3 OR ffluxlab|
|DISABLE_PROBLEMS|Disables printing out the problems at the top of the Main Menu|False|True or False|


