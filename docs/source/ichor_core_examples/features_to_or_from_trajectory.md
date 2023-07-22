## Converting to `Trajectory` from features

ichor can convert from a features `.csv` or `.xlsx` files to a trajectory instance. This trajectory instance can then be used to access coordinates of atoms or white to a `.xyz file`. converting to/from features can be useful if the user wants to modify the features in some way and then make
a `.xyz` file which can be used to submit `.gjf`/`.wfn` files to Gaussian or AIMALL.

To convert from a features file, we do

```python
from ichor.ichor_lib.files.trajectory import Trajectory

traj = Trajectory.features_file_to_trajectory("water_dimer_features_xlsx_file.xlsx", atom_types=["O", "H", "H", "O", "H", "H"])
```
or

```python
from ichor.ichor_lib.files.trajectory import Trajectory

traj = Trajectory.features_file_to_trajectory("water_dimer_features_csv_file.csv", atom_types=["O", "H", "H", "O", "H", "H"])
```

The `atom_types` is a list of atom types. It is important these are arranged in the correct order that matches the columns of the features in the `.csv` or `.xlsx` file. For example, the `"features_excel_file.xlsx"` file above will contain an excel sheet that has the following order of columns (the sheet name indicates which is the central atom). The first line of the `.csv` will also have the same ordering of the columns:

```
bond1, bond2, angle, r3, theta3, phi3, r4, theta4, phi4, r5, theta5, phi5
```

The `atom_types` is ordered as `["O", "H", "H", "O", "H", "H"]`, therefore we have an oxygen as the central atom, H atom as x-axis atom, H atom as xy-plane atom. Each of the other three remaining atoms are described with `r,theta,phi` components. The `atom_types` are a list of length 6, therefore there should be `3*6-6 = 12` features in the excel or csv file.

Now we have a trajectory instance so we can do things like

```python
print(traj.coordinates)
print(traj.features)
print(traj[0].features)
```
like a normal `Trajectory` instance (see the other example file for working with trajectories).

## Making custom trajectories

So let's say we have a features file for the water dimer and we only want to change the phi angles only. This can be useful for tracking the energy change along one dimension at a time. We can write another short script that modifies the phi angles columns in the features file and then convert it to a trajectory.

```python
import pandas as pd
import numpy as np

# df containing all WD geometries from tyche
initial_df = pd.read_excel("water_dimer_tyche_new_calculated_features.xlsx", sheet_name=0, index_col=0, header=0)

# only get the firs water dimer geometry
first_geometry = initial_df.values[0]

# make an array that adds to phi angles only (5, 8, 11 dims)
# adding linspace of 0 to 2pi will make a full rotation
angle_to_add = np.linspace(0, 2*np.pi, 1000)
array_to_add = np.zeros((1000,12))
array_to_add[:, 5] = angle_to_add
array_to_add[:, 8] = angle_to_add
array_to_add[:, 11] = angle_to_add

# add the first geometry to array that adds to phi dimensions only
geometries_phi_changed_only = first_geometry + array_to_add

new_df = pd.DataFrame(geometries_phi_changed_only, columns=initial_df.columns)
new_df.to_csv("water_dimer_phi_change_only.csv")
```

What we have done is taken a features file that contained a lot of water dimer geometries. We have taken the first geometry only and added an array which only modifies the phi features (which are the 5,8,11th columns as indeces start at 0). We have written this to a new features file that contains the modified features. The result is shown below. As you can see, one of the water molecules is stationary and the other is only rotating in the phi dimension.

Now we have a custom trajectory and we can run it through gaussian and Aimall like so

```python

from ichor.main.gaussian import submit_points_directory_to_gaussian
from ichor.ichor_lib.files.trajectory import Trajectory

traj = Trajectory.features_file_to_trajector("water_dimer_phi_change_only.csv",
                                             atom_types=["O", "H", "H", "O", "H", "H"])
traj.to_dir("./water_no_angle_change")
submit_points_directory_to_gaussian("./water_no_angle_change")
```

See the other example file for submitting multiple gjf or aimall files for details on batch Gaussian/Aimall submission with ichor.

## Using `PointsDirectory` to work with a folder containing points

We can use the `PointsDirectory` class as another way to write out `.xyz` files or `.xlsx` or `.csv` files with features. See the example for accessing output data from Gaussian/AIMALL calculations for more ways to use the `PointsDirectory` class to access things like energies or multipole moments.

We can do

```python

from ichor.ichor_lib.files import PointsDirectory

points = PointsDirectory("WD_phi_change_only")
```

then we can access coordinates or features of points by doing something like

```python
points.features
points["O1"].features
points[20].features
```

We can also write out feature of xyz files by doing

```python
point_dir.features_to_excel()
```
```python
point_dir.features_to_csv()
```

```
point_dir.coordinates_to_xyz()
```
See the arguments to the methods, such as being able to write out every nth point in the xyz file instead of writing out every single point.
