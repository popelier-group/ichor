# Submitting .gjf files to Gaussian or .wfn files to AIMALL using ICHOR

Since ICHOR can be used as a library, we can write a separate python script that uses ICHOR's modules to do tasks like submitting a lot of gjf files at once.

The `Trajectory` class can be used to convert a trajectory file (such as a `.xyz` or `DLPOLY History` that contain a lot of geometries) into individual `.gjf` files that are the inputs to Gaussian.

```python

from ichor.main.gaussian import submit_points_directory_to_gaussian
from ichor.ichor_lib.files.trajectory import Trajectory

traj = Trajectory("WATER.xyz")
traj.to_dir("./water_no_angle_change")
submit_points_directory_to_gaussian("./water_no_angle_change")
```

The `to_dir` method accepts a directory where all the `.gjf` are going to be written to. From that we can use the `submit_gjfs` function which accepts a path to a directory containing `.gjf` files.

`submit_gjfs` is a general purpose function that submits all `.gjf` files found in a directory, so it can be used to run any `.gjf` file that is set up by the user. It can be used on CSF3 or FFLUXLAB machines, as ICHOR is written to work on both.

## Deleting Jobs submitted via ICHOR or its modules

If a lot of jobs were submitted, the user can use ICHOR's Command Line Interface (CLI) to delete the jobs if needed.

```python
python ichor3.py
```

will open up ICHOR's CLI. Pressing `q` will open the `Queue Menu`. Entering `del` in that menu will delete the jobs that were submitted to the queuing system via ICHOR or its modules.

## Changing GLOBALS to use different Gaussian settings

ICHOR's Globals handle all the settings that various programs use. Gaussian has a lot of different keywords that are used to select what calculations Gaussian does. These keywords select things like the level of theory, basis sets, molecular optimization settings and many as and many others.

For example, if we want to change the Gaussian core count that is used for the job, we can do:

```python
from ichor.main.gaussian import submit_points_directory_to_gaussian
from ichor.globals import GLOBALS
from ichor.ichor_lib.files.trajectory import Trajectory

GLOBALS.GAUSSIAN_CORE_COUNT = 4

traj = Trajectory("WATER.xyz")
traj.to_dir("./water_testing_globals")
```

Going into one of the .gjf files shows that the `%nproc` keyword Gaussian uses to select the number of cores for a calculation is set to `4` instead of `2` (which is the default).

```
%nproc=4
%mem=1GB
#p B3LYP/6-31+g(d,p) nosymm output=wfn

SYSTEM0001

0 1
O       0.00000000      0.00000000      0.00000000
H       1.01294606      0.00000000      0.00000000v
H      -0.54588097      0.94549358      0.00000000

water_testing_globals/SYSTEM0001.wfn
```

See `ichor/globals/globals.py` file which contains a table with all the different settings that can be changed from by GLOBALS.

# Submitting AIMALL jobs

Now that we have ran Gaussian, we should have `.wfn` files which can be passed into AIMALL. After the Gaussian jobs are finished we can do

```python
from ichor.main.aimall import submit_points_directory_to_aimall

submit_points_directory_to_aimall("./water_no_angle_change", atoms=None)
```

This will queue up AIMALL jobs for all the .wfn files that were found in the given directory.