# Submitting .gjf files to Gaussian or .wfx files to AIMALL using ichor.hpc

Since ICHOR can be used as a library, we can write a separate python script that uses `ichor`'s modules to do tasks like submitting a lot of gjf files at once.

The `ichor.core.files.Trajectory` class can be used to convert a trajectory file (such as a `.xyz` or `DLPOLY History` that contain a lot of geometries) into individual `.xyz` files that are the inputs to Gaussian.

```python

from ichor.main.gaussian import submit_points_directory_to_gaussian
from ichor.core.files import Trajectory, PointsDirectory

traj = Trajectory("WATER.xyz")
# make into a directory containing individual .xyz files
traj.to_dir("water_no_angle_change")
pd = PointsDirectory("water_no_angle_change")
submit_points_directory_to_gaussian(pd)
```

The `to_dir` method makes a directory containing individual `.xyz` files that were split from
the trajectory. Then the `PointsDirectory` can parse this directory and make individual
directories for each `.xyz` file. Finally, `submit_points_directory_to_gaussian` submits the
Gaussian array job to a compute cluster.

## Submitting AIMALL jobs

Now that we have ran Gaussian, we should have `.wfx` files which can be passed into AIMALL. After the Gaussian jobs are finished we can do

```python
from ichor.main.aimall import submit_points_directory_to_aimall

submit_points_directory_to_aimall("water_no_angle_change")
```

This will queue up AIMALL jobs for all the .wfx files that were found in the given directory.

AIMAll reads the calculation method from the WFX `<Model>` section. Ichor preserves
that section when it is present. When it is missing, Ichor uses the method from the
point's Gaussian input, or the `method` argument (default `B3LYP`) if the input
method is unavailable.

For older point directories with only WFN output, submit the points to Gaussian
again to generate WFX before submitting them to AIMAll. Ichor updates legacy
Gaussian wavefunction directives when preparing the submission.
