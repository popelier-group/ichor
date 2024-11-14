Supported File Formats
======================

.. list-table:: **AIMALL**
   :widths: 8 50 10
   :header-rows: 1

   * - File Type
     - Description
     - Role
   * - .aim
     - Contains information about the calculation e.g. settings and timings.
     - Output
   * - .int
     - Result file from calculating a set of atomic properties.
     - Output
   * - .wfn
     - AIM traditional wavefunction file.
     - Input
   * - .wfx
     - AIM extended wavefunction file.
     - Input

.. list-table:: **AMBER**
   :widths: 8 60 10
   :header-rows: 1

   * - File Type
     - Description
     - Role
   * - .in
     - Defines the simulation parameters for AMBER molecular dynamics.
     - Input

.. list-table:: **CP2K**
   :widths: 8 60 10
   :header-rows: 1

   * - File Type
     - Description
     - Role
   * - .inp
     - Defines the simulation parameters for CP2K molecular dynamics.
     - Input

.. list-table:: **DL_Poly (DP) / DL_FFLUX (DF)**
   :widths: 8 50 10
   :header-rows: 1

   * - File Type
     - Description
     - Role
   * - CONFIG
     - Contains the geometry information of the system.
     - Input (DP, DF)
   * - CONTROL
     - Defines the control parameters used to run a simulation.
     - Input (DP, DF)
   * - FIELD
     - The dump file of atomic coordinates, velocities and forces.
     - Output (DP, DF)
   * - HISTORY
     - Contains information about the calculation e.g. settings and timings.
     - Output (DP, DF)
   * - IQA_ENERGIES
     - Contains information about the calculation e.g. settings and timings.
     - Output (DF)
   * - IQA_FORCES
     - Contains the IQA forces from FFLUX.
     - Output (DF)

.. list-table:: **Gaussian**
   :widths: 8 50 10
   :header-rows: 1

   * - File Type
     - Description
     - Role
   * - .gau, .gaussianoutput
     - Contains coordinates (in Angstroms), forces and molecular multipole moments.
     - Output
   * - .gjf
     - Defines input parameters, method, basis set etc. for Gaussian calculations.
     - Input
   * - .wfn
     - AIM traditional wavefunction file.
     - Input
   * - .wfx
     - AIM extended wavefunction file.
     - Input

.. list-table:: **MORFI**
   :widths: 8 50 10
   :header-rows: 1

   * - File Type
     - Description
     - Role
   * - .mout
     - Output file for in-house code MORFI.
     - Output
     * - .pandora
     - Input file for in-house code MORFI.
     - Input

.. list-table:: **ORCA**
   :widths: 8 50 10
   :header-rows: 1

   * - File Type
     - Description
     - Role
   * - .engrad
     - Contains the energy and gradient calculated by ORCA.
     - Output
   * - .orcainput
     - Contains input parameters, method, basis set, molecular structure etc.
     - Input
   * - .orcaoutput
     - Contains information such as coordinates and molecular dipoles/quadrupoles.
     - Input

.. list-table:: **Other**
   :widths: 8 50
   :header-rows: 1

   * - File Type
     - Description
   * - .model
     - A model file from a machine learning program, such as FEREBUS.
   * - .sh
     - Job submission scripts for various programs such as Gaussian and AIMALL.
   * - .xyz
     - A file containing molecular dynamics trajectories.

++++++++
Workflow
++++++++
.. image:: /extra_files/WORKFLOW.png
