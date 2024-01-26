Setting up ichor_config.yaml
================================

You will need to create a .yaml file containing ichor config variables
in order to specify executable paths, any modules that need to be loaded on the cluster,
and other parameters which are needed for ichor.

An example ichor_config.yaml is provided in the ichor's GitHub repository
and can also be downloaded below.

.. note::
    The config file is likely to be updated as more functionality is added.

This following structure is currently implemented in the .yaml file:

.. code-block:: text

    csf3:   # this is the name of machine which ichor is running on.
            # ensure that the name of the machine is contained in hostname or platform.node (in Python)

      hpc:    # any parameters relating to queue system

        parallel_environments:
          smp.pe: [2, 32]

      software:  # any parameters relating to a program

        gaussian:  # an example program name
          executable_path: "$g09root/g09/g09"    # the absolute path to the executable on the cluster
          modules: ["apps/binapps/gaussian/g09d01_em64t"]  # a list of modules to be loaded. If not present, no modules are loaded

:download:`ichor config example <../../ichor_config.yaml>`
