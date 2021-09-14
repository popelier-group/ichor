# Working with trajectory files

There are multiple formats for trajectory files, the ones we use are either `.xyz` files or `DLPOLY History` files. Trajectory files contain multiple timesteps, with each timestep containing a different geometries of a chemical system. An `.xyz` file has the following format (see [this Wikipedia page](https://en.wikipedia.org/wiki/XYZ_file_format) for details)

```
       6
 i =        0
  C        -2.2784429253        0.3764716548        0.0613600732
  H        -1.1673363228        0.3433523315        0.0589783963
  O        -2.7413739998        1.2129700870       -0.9589752442
  H        -2.6620523911        0.7204890516        1.0463251752
  H        -2.6560170817       -0.6512416081       -0.1176831528
  H        -2.3804869890        2.1150657510       -0.7572121286
       6
 i =        1
  C        -2.2863781387        0.3834087333        0.0531928455
  H        -1.1942737791        0.3301522963        0.0224285724
  O        -2.7366005255        1.2110852658       -0.9560297206
  H        -2.6062423767        0.7046732375        1.0558981292
  H        -2.6462066446       -0.6636062224       -0.0697004711
  H        -2.3946286419        2.1003419571       -0.7288986971
       6
 i =        2
  C        -2.2939466970        0.3894321047        0.0456932982
  H        -1.2146859241        0.3150121443       -0.0104391934
  O        -2.7315553621        1.2091993502       -0.9540227847
  H        -2.5510984567        0.6896104431        1.0693639362
  H        -2.6378315944       -0.6723766313       -0.0245673363
  H        -2.4098627840        2.0863041759       -0.7030934029
```

## The `Trajectory` class
The trajectory class allows us to work with `.xyz` files containing timesteps with different molecular geometries. Each atom in a molecular geometry has its own set of features (there are 3N-6 features, where N is the number of atoms in the system.)

To read in a trajectory file, do 
```python
from ichor.files.trajectory import Trajectory

# Trajectory("path_to_trajectory_file")
traj = Trajectory("METHANOL_for_testing.xyz")
```

This automatically parses the trajectory file. Now we can access important attributes, such as atom names, coordinates, and features.


## Atom names
Accessing names of atoms. These have indices because we need to be able to distinguish between atoms which are of the same element.
```python
print(traj.atom_names)  # returns a list of atom names as strings
```
```
Output:
['C1', 'H2', 'O3', 'H4', 'H5', 'H6']
```

## Coordinates
We can also access the xyz coordinates of each atom.

```python
print(traj.coordinates)
```
This will give back a numpy 3D array of shape `n_timesteps, n_atoms, 3`. We can then index into the numpy array:

```python
print("First timestep coordinates")
print(traj.coordinates[0])
print()
print("First atom in first timestep coordinates")
print(traj.coordinates[0][0])
```
```
Output:

First timestep coordinates
[[-2.27844293  0.37647165  0.06136007]
 [-1.16733632  0.34335233  0.0589784 ]
 [-2.741374    1.21297009 -0.95897524]
 [-2.66205239  0.72048905  1.04632518]
 [-2.65601708 -0.65124161 -0.11768315]
 [-2.38048699  2.11506575 -0.75721213]]

First atom in first timestep coordinates
[-2.27844293  0.37647165  0.06136007]
```
These have shapes `n_atoms, 3` and `3,` respectively.

## Indexing coordinates by atom names
We can alternatively index the trajectory by the atom names instead

```python
print("C1 coordinates")
print(traj["C1"].coordinates)
```
```
Output:
C1 coordinates
[[-2.27844293  0.37647165  0.06136007]
 [-2.28637814  0.38340873  0.05319285]
 [-2.2939467   0.3894321   0.0456933 ]
 [-2.30089362  0.39392328  0.03925431]
 [-2.30676353  0.39640999  0.03437357]]
```
This gives back the coordinates of atom `C1` only as a numpy array of shape `n_timesteps, 3`. Again, we can further index into this array, this time we have to options, both should give the same result.

```python
print("C1 coordinates for first timestep")
print(traj["C1"][0].coordinates)
```
```
Output:
C1 coordinates for first timestep
[-2.27844293  0.37647165  0.06136007]
```

```python
print("C1 coordinates for first timestep")
print(traj["C1"].coordinates[0])
```
```
Output:
C1 coordinates for first timestep
[-2.27844293  0.37647165  0.06136007]
```
## Slicing coordinates

Slicing is also supported, so we can do something like

```python
print("Timestep coordinates of all atoms for the first two timesteps")
print(traj[:2].coordinates)
```
```
Output:
Timestep coordinates of all atoms for the first two timesteps
[[[-2.27844293  0.37647165  0.06136007]
  [-1.16733632  0.34335233  0.0589784 ]
  [-2.741374    1.21297009 -0.95897524]
  [-2.66205239  0.72048905  1.04632518]
  [-2.65601708 -0.65124161 -0.11768315]
  [-2.38048699  2.11506575 -0.75721213]]

 [[-2.28637814  0.38340873  0.05319285]
  [-1.19427378  0.3301523   0.02242857]
  [-2.73660053  1.21108527 -0.95602972]
  [-2.60624238  0.70467324  1.05589813]
  [-2.64620664 -0.66360622 -0.06970047]
  [-2.39462864  2.10034196 -0.7288987 ]]]
```
This is a 3D array of shape `2, n_atoms, 3` as we only requested the first `2` timesteps from the trajectory.

We can also do slicing for a specific atom like so. Either of the two ways below gives the same result.

```python
print("C1 coordinates for first two timesteps")
print(traj["C1"][:2].coordinates)
```
```
Output:
C1 coordinates for first two timesteps
[[-2.27844293  0.37647165  0.06136007]
 [-2.28637814  0.38340873  0.05319285]]
```

```python
print("C1 coordinates for first two timesteps")
print(traj["C1"].coordinates[:2])
```
```
Output:
C1 coordinates for first two timesteps
[[-2.27844293  0.37647165  0.06136007]
 [-2.28637814  0.38340873  0.05319285]]
```
These are 2D numpy arrays of shape `2, 3`. In general, the shape will be `n_timesteps, 3`, depending on the slice length.


## Features
Each atom has its own set of features. We can get the atom features by doing

```python
print("All features")
print(traj.features)
```

This will output a 3D numpy array of shape `n_timesteps, n_atoms, 3N-6`. For methanol we have 6 atoms in the system, so `3 * 6 - 6 = 12` features.

We can also use atom names to index the features, so we can do

```python
print("O3 features only")
print(traj["O3"].features)
```
```
Output:
O3 features only
[[ 2.6423203   1.87523721  1.84945923  3.90495307  2.02968561  0.27265601
   3.90495306  1.11190703  0.27265598  3.86833143  1.57079634 -0.53841719]
 [ 2.60910814  1.85088109  1.83476052  3.8320903   2.04948579  0.24484427
   3.92831295  1.1492169   0.29153819  3.92236262  1.5514919  -0.51976965]
 [ 2.57928713  1.82802512  1.82136865  3.77510983  2.06875272  0.21548588
   3.96240519  1.18677666  0.30912101  3.96977432  1.5328657  -0.50130248]
 [ 2.55486817  1.81747545  1.80988638  3.74071572  2.08825136  0.18563454
   4.00645064  1.22311895  0.32619514  4.00651071  1.51468696 -0.48380198]
 [ 2.53810945  1.82465214  1.80068306  3.73050394  2.10769769  0.15570992
   4.05604828  1.25737486  0.34285898  4.0301657   1.49661818 -0.46817998]]
```
which is a 2D numpy array (matrix) of shape `n_timesteps, n_features` for atom `O3` only.

Again, we can index further into this numpy array by either of the two ways below

```python
print("O3 features for first timestep only")
print(traj["O3"][0].features)
print(traj["O3"].features[0])
```
```
Output:
O3 features for first timestep only
[ 2.6423203   1.87523721  1.84945923  3.90495307  2.02968561  0.27265601
  3.90495306  1.11190703  0.27265598  3.86833143  1.57079634 -0.53841719]
[ 2.6423203   1.87523721  1.84945923  3.90495307  2.02968561  0.27265601
  3.90495306  1.11190703  0.27265598  3.86833143  1.57079634 -0.53841719]
```
which is a 1D numpy array of shape `n_features,`, containing the features for atom `O3` for only the first timestep in the trajectory.

## Slicing features

Features can be sliced in exactly the same ways as coordinates.

```python
print("C1 features for first two timesteps")
print(traj["C1"][:2].features)
```
```
Output:
C1 features for first two timesteps
[[ 2.6423203   2.10062456  1.92536997  2.10062456  2.4785883  -2.17012751
   2.09650041  0.59032738 -2.19149957  3.6365239   2.02118226  0.26669858]
 [ 2.60910814  2.06704824  1.91155256  2.07950764  2.45912327 -2.25011152
   2.10500531  0.60387504 -2.29799249  3.57115494  2.04128028  0.23985385]]
```

```python
print("C1 features for first two timesteps")
print(traj["C1"].features[:2])
```
```
Output:
C1 features for first two timesteps
[[ 2.6423203   2.10062456  1.92536997  2.10062456  2.4785883  -2.17012751
   2.09650041  0.59032738 -2.19149957  3.6365239   2.02118226  0.26669858]
 [ 2.60910814  2.06704824  1.91155256  2.07950764  2.45912327 -2.25011152
   2.10500531  0.60387504 -2.29799249  3.57115494  2.04128028  0.23985385]]
```
Both ways will give the same 2D numpy array of shape `2, 12`. In general, the array will be of shape `n_timesteps, n_features`. The `n_timesteps` depends on the slice length that is given. The `n_features` depend on the size of the system, determined by `3 * N - 6`.


## DLPOLY History Files

DLPOLY History Files contain the same information as `.xyz` files, with the only difference being that they need to be parsed differently initially. After that, the coordinates and features can be accessed the same way as in the `Trajectory` class.

```python
from ichor.files.dlpoly_history import DlpolyHistory

traj = DlpolyHistory("DLPOLY_history_file_location")
```



