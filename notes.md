# ICHOR Notes

## TODO

### Order of Operations
1. Make lib watertight
2. Update HPC to remove GLOBALS
3. Update CLI to use new HPC and lib

### Short-Term
- ichor.ichor_cli -> ichor.cli ...
- Fix INT file
- INTs rotate multipoles
- Improve Cahn-Ingold-Prelog (find standard BFS implementation)
- INTs replace with ordered dictionary
- GLOBALS -> config (remove globals in favour of config that gets passed to other places)
- Add SLURM support

### Long-Term
- Know how the ALF affects the models
- Remove parent from INT
- ReadFile, WriteFile
- AIMAll AB (and AA')
- HPC 17,500 job limit?

### Ideas
- !!!!!!!!!!! Need Tests !!!!!!!!!!!
- Refactor Menu to make it easier to write refreshable menus
- Need to get the time to initialise down
- ichor.core.common -> ichor.core.util

## Architecture

### ichor.core
`ichor.core` should not rely on any state and should have little to no side-effects.
`core` is a pure library and should not rely on any other parts of `ichor`

### ichor.hpc
`ichor.hpc` is still a library but has a state based upon a config and the machine being ran on.
The goal would be to remove the state but this is not always possible, I wonder whether
some parts could still be moved to `ichor.core` and then used by `ichor.hpc`

### ichor.cli
`ichor.cli` is not intended to be used as a library but instead builds on top of `ichor.hpc`
and `ichor.core` to provide the `ichor` functionality as an application.


### Possible decisions
- [x] Menu and TabCompleter -> core
- [ ] Separate Model from ModelFile, ModelFile -> core.files
- [ ] Not a fan of general_menus
- [ ] daemon -> core
- [ ] active_learning -> core?
- [ ] both qcp and qct hpc.main -> hpc.programs?
- [ ] cli menus directory structure should follow tree of main menu?
- [ ] DLPOLY -> DL_FFLUX