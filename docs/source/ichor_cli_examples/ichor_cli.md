# Submitting AIMAll from the command line

Install or update `ichor-cli` to register the `ichor` command (for a source
checkout, run `pip install -e ./ichor_cli`). Submit an existing points directory:

```sh
ichor submit_aimall water.pointsdir --method B3LYP --ncores 4 --naat 2 --encomp 3
ichor submit_aimall water.pointsdir --atoms O1 H2 --force --no-iasprops
ichor submit_aimall --help
```

The directory defaults to the current working directory, which must be a
`.pointsdir`. Submission uses the existing HPC configuration in
`~/ichor_config.yaml` and the configured scheduler. Help does not require HPC
configuration. Defaults match the Python submission API. Boolean AIMAll settings
accept `--setting` and `--no-setting`; `--atidsprops some` selects 0.001.
Use `--hold JOB_ID` to wait for another scheduler job, and `--script-name`,
`--outputs-dir-path`, or `--errors-dir-path` to override submission paths.
The command reports the submitted job ID or that no jobs require submission.

# Launching the Menu

After installing `ichor.cli`, it can be launched from the command line using `ichor-cli`. Many common tools to submit jobs are available in the command line interface (CLI). Behind the scenes, the `console-menu` package is used to make the menus.

Below is an example of what the menu structure looks like. Selecting options and pressing `Enter` leads to sub-menus with more options. The most common options are shown in the menus, not all of the functionality is available through the menus. However, one can complete all steps starting from making a dataset (using AMBER, CP2K) to running Gaussian and AIMAll, to making datasets for machine learning from the menus.

![alt text](../../../example_files/ichor_cli_main_menu.png "Ichor main menu")
