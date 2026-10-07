# ICHOR CLI SUBPACKAGE

This is the subpackage that contains ichor menus. It forms the command line interface utilities that allow users to easily do common things on HPC machines (as defined in the hpc subpackage).

`ichor workflow [ichor_workflow.yaml]` runs optimisation with ASE/xTB,
metadynamics with ASE/PLUMED/xTB, diversity sampling with POLUS, then the existing
Gaussian → AIMAll → optional SQLite/CSV data generation stages.
Machine and executable settings remain in `ichor_config.yaml`.

Choose the parts to run with `--stages`, or `workflow.stages` in YAML. Supported
stages are `optimisation`, `metadynamics`, `diversity`, and `datagen`. Only selected
stages run, always in that order; stages can be skipped. CLI selection overrides
the YAML list. For example:

```sh
ichor workflow --stages optimisation
ichor workflow --stages metadynamics diversity
ichor workflow --stages optimisation datagen
ichor workflow --stages datagen
```

For YAML selection, use `workflow.stages: [metadynamics, diversity]`. Omitting the
list runs all four stages; empty lists and duplicate stages are rejected.

For each invocation, set `input.path` to the input of its first stage: a structure
for optimisation/metadynamics, a trajectory for diversity, or a sampled trajectory
or existing `.pointsdir` for datagen. When starting at diversity, also supply
`diversity.seed_geom`, the reference structure. Relative paths are resolved against
the YAML directory. Configure collective variables for your molecule and set
`diversity.output` to the actual sampled XYZ filename produced by your POLUS version.

Keep the command running on the login node while intermediate scheduler jobs
finish; it prepares the following stage only after successful completion. The
last requested stage is submitted without waiting. Ctrl-C prevents further
submissions and leaves submitted jobs running; use the scheduler to cancel those
jobs if needed. Resume with the next stage and its input path. Existing stage
outputs are protected from replacement; use a new workflow directory and output
paths for a fresh run. `ichor datagen` and `ichor submit_datagen` still submit only
data generation using `input.path`.
