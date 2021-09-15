# Accessing Output data of Gaussian or AIMALL calculations
After running Gaussian or AIMALL calculations, we can access things such as the energy calculated by Gaussian or the IQA energy or multipole moments calculated by AIMALL.

To access these properties for all .wfn or all .int files in a directory, we can use the `PointsDirectory` class. This class wraps around a directory, containing multiple points. Each point is wrapped with the `PointDirectory` class. We can work with the `PointsDirectory` class directly as it loops through all the subsequent subdirectories and looks for `.wfn` and `.int` files.

If Gaussian and AIMALL calculations were done using ICHOR or your own script that uses ICHOR's modules (see `submitting_multiple_gjfs` example), the resulting directory structure looks something like this (where `.` indicates the directory where job outputs were written to.)

## Directory Structure of ICHOR's Gaussian and AIMALL calculations

Below is the directory structure that ICHOR produces when running Gaussian and AIMALL calculations. Note that only part of the tree structure is shown.

```
.
├── SYSTEM0001
│   ├── SYSTEM0001_atomicfiles
│   │   ├── h2.int
│   │   ├── h2.int.bak
│   │   ├── h3.int
│   │   ├── h3.int.bak
│   │   ├── o1.int
│   │   └── o1.int.bak
│   ├── SYSTEM0001.gjf
│   └── SYSTEM0001.wfn
├── SYSTEM0002
│   ├── SYSTEM0002_atomicfiles
│   │   ├── h2.int
│   │   ├── h2.int.bak
│   │   ├── h3.int
│   │   ├── h3.int.bak
│   │   ├── o1.int
│   │   └── o1.int.bak
│   ├── SYSTEM0002.gjf
│   └── SYSTEM0002.wfn
...
...
...
```

Each `SYSTEM*` directory is one molecular geometry for which `.wfn` and `.int` files made with Gaussian or AIMALL. The naming of the system can be changed by using ICHOR's `GLOBALS`. The AIMALL output files `.int` are parsed and renamed to `.int.bak`. New `.int` files are written in `json` format to speed up data loading, which contain all the iqa and multipole moment information we need.

To get the energy of all `.wfn files`, we can do

```python
from ichor.points.points_directory import PointsDirectory

# PointsDirectory("path_to_directory_with_wfn_and_int_files")
points_dir = PointsDirectory("water_small_dataset")
print(points_dir.energy)
```

which will give back a list of energies for all `.wfn` files found in the directory given to `PointsDirectory`
```
[-76.414276787755, -76.416516489879, -76.377032512632, -76.376168990344, -76.4018192777, -76.425298429018, -76.405772024379, -76.402147429468, -76.386609031197]
```

## IQA energy

Accessing iqa energies is done by

```python
print(points_dir.iqa)
```
which gives back a list of dictionaries. Each element in the list is a dictionary that contains the IQA energies of all topological atoms for one molecular geometry.
```
[{'O1': -75.454100818, 'H2': -0.48238887116, 'H3': -0.47778358984}, {'O1': -75.454709649, 'H2': -0.47741211522, 'H3': -0.48438435291}, {'O1': -75.424754363, 'H2': -0.472579711, 'H3': -0.47969937988}, {'O1': -75.428668531, 'H2': -0.47434796495, 'H3': -0.47315622181}, {'O1': -75.444637139, 'H2': -0.48315330875, 'H3': -0.47402110252}, {'O1': -75.460788616, 'H2': -0.48353015219, 'H3': -0.48097446655}, {'O1': -75.447031704, 'H2': -0.48441841526, 'H3': -0.47431286322}, {'O1': -75.444669271, 'H2': -0.48376332931, 'H3': -0.47370494591}, {'O1': -75.433557169, 'H2': -0.47323542532, 'H3': -0.47981524311}]
```

## Multipole moments

Accessing multipole moments is done by

```python
print(points_dir.multipoles)
```

This is a list of dictionaries. Each dictionary contains `key`:`value ` pairs, with the `key` corresponding to the atom name (such as `O1`, `H2`, etc.) and the `value` being a dictionary containing all the multipole information for that particular topological atom. This dictionary has `key`:`value` pairs with the `key` being a multipole name (such as `q00`, `q32s`, etc. ) and the `value` corresponding to the AIMALL calculated value for that multipole moment.

```
[{'O1': {'q00': -9.1249874044, 'q10': 4.7027176792e-06, 'q11c': -0.098995982288, 'q11s': -0.13306312538, 'q20': -0.69327861912, 'q21c': 1.0160348589999998e-05, 'q21s': 2.2677974883999997e-05, 'q22c': 1.050592694844688, 'q22s': -0.5008168443199998, 'q30': -0.00010264137628, 'q31c': -0.13824820684219988, 'q31s': -0.26925885475954786, 'q32c': -2.2505038152999994e-05, 'q32s': 2.6946609080999997e-05, 'q33c': 0.9892384157600002, 'q33s': -0.024354625717999987, 'q40': 1.6830761236, 'q41c': -0.00050121906838, 'q41s': -5.466781397200001e-05, 'q42c': -0.48417880315999995, 'q42s': 0.76211790439, 'q43c': 0.00035793391824, 'q43s': -1.4269870219999996e-05, 'q44c': 1.3453448249999997, 'q44s': 2.1169008095}, 'H2': {'q00': -0.41748130728, 'q10': -4.8094090872e-07, 'q11c': 0.16258491847, 'q11s': -0.010422943989, 'q20': 0.0046620174203, 'q21c': 3.9806975477999995e-07, 'q21s': 5.580327579199999e-07, 'q22c': -0.010151454269553859, 'q22s': 0.023170264023, 'q30': -4.403896474e-07, 'q31c': 0.06643764016895522, 'q31s': 0.006320135837264717, 'q32c': 1.9707410116e-07, 'q32s': -6.1740618367e-07, 'q33c': -0.11511390476000001, 'q33s': -0.03181189169100001, 'q40': 0.12735449451, 'q41c': 3.6055635037000004e-06, 'q41s': 9.238262402800001e-07, 'q42c': -0.17839068698, 'q42s': -0.0048614500624, 'q43c': -1.6550989369e-06, 'q43s': -1.5939328024999996e-07, 'q44c': 0.20248475169, 'q44s': 0.00096954662549}, 'H3': {'q00': -0.45752494449, 'q10': 6.4430787118e-08, 'q11c': 0.15559118682777226, 'q11s': -0.015941873586903965, 'q20': -0.015387054787, 'q21c': 8.718964732802425e-09, 'q21s': -5.043005268832772e-07, 'q22c': 0.020572829896047695, 'q22s': 0.04260900199514434, 'q30': -5.5745863651e-08, 'q31c': 0.08662784021323013, 'q31s': 0.004946929092473042, 'q32c': -3.596192767681956e-07, 'q32s': 8.04063471584192e-07, 'q33c': -0.1482703183928764, 'q33s': -0.022534118056844125, 'q40': 0.11406342802, 'q41c': 3.903341349397345e-06, 'q41s': -4.345286217179838e-06, 'q42c': -0.1560999360377987, 'q42s': 0.011224350439722712, 'q43c': 2.2069965348771971e-07, 'q43s': -1.1541758009611276e-06, 'q44c': 0.167204891546376, 'q44s': -0.04374788161760213}}, {'O1': {'q00': -9.1665642501, 'q10': -2.3059599406e-06, 'q11c': -0.068177641589, 'q11s': -0.15044728107, 'q20': -0.66866488714, 'q21c': 4.099627118499999e-06, 'q21s': -1.6903874436e-05, 'q22c': 1.0759063816858594, 'q22s': -0.4618038609899999, 'q30': 6.888204875e-05, 'q31c': -0.16507415920850263, 'q31s': -0.23971775513956112, 'q32c': 6.015380261799999e-05, 'q32s': 7.0335354374e-05, 'q33c': 0.9438987428300001, 'q33s': 0.03319954808900001, 'q40': 1.7131984276, 'q41c': -1.2370073923000002e-05, 'q41s': 0.000274880104, 'q42c': -0.4594023970599999, 'q42s': 0.84378895946, 'q43c': 9.8801809539e-05, 'q43s': 9.8971016693e-05, 'q44c': 1.0751467831999997, 'q44s': 2.1388263984}, 'H2': {'q00': -0.44953576232, 'q10': 3.3609746559e-07, 'q11c': 0.15422778997, 'q11s': -0.015724804507, 'q20': -0.013316743733, 'q21c': -5.323688924899999e-07, 'q21s': -9.537154367799999e-08, 'q22c': 0.04192636479795362, 'q22s': 0.026566722994999997, 'q30': 1.4529061986e-06, 'q31c': 0.08332371824540057, 'q31s': 0.004974408906597709, 'q32c': -9.686102900800001e-08, 'q32s': 2.9493595543e-07, 'q33c': -0.14417319029000003, 'q33s': -0.021924244381999997, 'q40': 0.11334101577, 'q41c': -4.5477791377e-06, 'q41s': -2.1294194546000004e-06, 'q42c': -0.15634281819, 'q42s': 0.0099358892264, 'q43c': 1.369125067e-06, 'q43s': -8.8412434551e-07, 'q44c': 0.16849544208, 'q44s': -0.041605575728}, 'H3': {'q00': -0.38389436241, 'q10': -2.2111323496999998e-07, 'q11c': 0.16205011760229962, 'q11s': -0.006436547636829659, 'q20': 0.020576070018999998, 'q21c': 1.6666904529275446e-07, 'q21s': -7.329329661154025e-07, 'q22c': -0.01959441454504045, 'q22s': -0.0024342003652153815, 'q30': -3.932704599899999e-07, 'q31c': 0.04167766642476307, 'q31s': 0.006465041458128612, 'q32c': -1.3991538226312745e-07, 'q32s': 5.516857457942293e-07, 'q33c': -0.07456849330286322, 'q33s': -0.03335940816136265, 'q40': 0.11396028364999994, 'q41c': 1.0013991549446983e-06, 'q41s': -8.895142067339649e-07, 'q42c': -0.16223034209633044, 'q42s': -0.01631601023990422, 'q43c': -6.129865999105113e-07, 'q43s': 9.547596568623968e-07, 'q44c': 0.1905533016211626, 'q44s': 0.03283063254663491}}]
```

