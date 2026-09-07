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

Letting ichor read the cluster's settings
+++++++++++++++++++++++++++++++++++++++++

On a SLURM cluster, the whole ``hpc`` block can be read from the queue rather than
written by hand:

.. code-block:: text

    ichor-config-init --detect

This runs ``sinfo``, and writes a config for this cluster with the partitions, the
memory per core and the time limit already filled in. It has to be run somewhere
``sinfo`` works, which normally means a login node, and it only works on SLURM --
the SGE equivalents differ too much between sites to guess at.

Two things it cannot do for you, and says so when it finishes:

* **The machine key.** It is guessed from the hostname, preferring the domain part,
  because the key has to appear in the hostname of the *compute* nodes as well and
  those differ from the login node. Check it against a compute node.
* **The software block.** Where each program lives and which module loads it is not
  something the queue knows. A skeleton is written out for you to fill in, and
  ``module avail`` lists what the cluster has.

The generated config gives the default partition the whole range of core counts.
Splitting the range between partitions is a decision about which job sizes belong
where, which is the site's to make, so the other partitions are listed as comments
with their core counts rather than guessed at.

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

The ``hpc`` block
-----------------

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Key
     - Default
     - What it is
   * - ``parallel_environments``
     - none
     - How a job's core count picks what to ask the queue for. Each key is the name
       of a SLURM **partition** (or an SGE parallel environment) and the value is the
       ``[minimum, maximum]`` range of cores to use it for. Every core count you
       submit with has to fall in one of the ranges, including one core jobs.
   * - ``memory_per_core_gb``
     - ``4``
     - How much memory one core brings on this machine. Jobs are sized around it,
       and Gaussian is told how much to use from it. The default is deliberately
       small and warns when it is used, as asking for more memory than a core
       actually brings gets the job killed.
   * - ``max_walltime``
     - ``7-0``
     - How long jobs may run for, written as the batch system wants it (``7-0`` or
       ``24:00:00``). SLURM rejects a job asking for longer than its partition
       allows, so a cluster with a shorter limit must set this. ``none`` leaves the
       limit out of the submission script so the partition's own default applies.

On a SLURM cluster these three come from the queue itself:

.. code-block:: text

    sinfo -o "%P %c %m %l"    # partition, cores per node, memory per node, time limit

which gives the partition names and core counts for ``parallel_environments``, the
time limit for ``max_walltime``, and enough to work out ``memory_per_core_gb`` (the
memory of a node divided by its cores).

The full example that ``ichor-config-init`` writes out is below.

:download:`ichor config example <../../ichor_hpc/ichor/hpc/data/config_template.yaml>`
