Setting up the ichor config file
================================

ichor reads the settings for each HPC cluster you run on -- executable paths, the
modules that need loading, and the parallel environments the queue offers -- from a
YAML config file.

Creating the file
-----------------

After installing ichor, run

.. code-block:: text

    ichor-config-init

This writes an example config file to ``~/.config/ichor/config.yaml``, which is
where ichor looks for it, and prints the path it wrote to. Open that file and edit
the block for the cluster you are on before submitting any jobs.

If you have used an older version of ichor and already have an
``~/ichor_config.yaml``, the same command moves it to the new location rather than
overwriting it with the example.

.. note::
    The config file is likely to be updated as more functionality is added.

Where ichor looks for the config file
-------------------------------------

The following locations are searched, in order, and the first config file that
exists is used:

1. the file named by the ``ICHOR_CONFIG`` environment variable, if it is set
2. ``$XDG_CONFIG_HOME/ichor/config.yaml``, which is ``~/.config/ichor/config.yaml``
   unless ``XDG_CONFIG_HOME`` is set to something else
3. ``~/ichor_config.yaml``

The third location is where the config file used to have to live. It is still read
so that existing installations keep working, but doing so warns, and the file
should be moved to the second location with ``ichor-config-init --migrate``.

Setting ``ICHOR_CONFIG`` is useful for pointing several users at one shared config
file, or for running against a config other than your own without moving anything.

What goes in the config file
----------------------------

Each top level key is the name of a machine. ichor picks the block to use by
looking for a key whose name appears in the hostname, so one config file covers
every cluster you run on and no per-machine copies are needed.

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

If ichor cannot find a block matching the machine it is running on, it warns on
startup and will not know how to run any of the programs.

The full example that ``ichor-config-init`` writes out is below.

:download:`ichor config example <../../ichor_hpc/ichor/hpc/data/config_template.yaml>`
