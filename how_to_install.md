# Installing ichor namespace packages

ICHOR package is split into three separate subpackages - core, hpc, cli. The core package has classes and methods for reading in files. The hpc package contains functions which are used to submit jobs on clusters such as CSF3/CSF4. The cli package is the command line interface package with useful commands and options which allow ease of use. The cli package uses the hpc and core packages.

# Installing core subpackage

To install the core subpackage, you will need to first have to make a new conda environment on csf3.

## Loading in anaconda on csf3

```
module load apps/binapps/anaconda3/2020.07
```

Then you will need to do

```
conda activate base
```
which will make `(base)` show up next to command line on terminal.

If the terminal tells you that `conda has not been properly initialized`, then do

```
conda init
```

## Making new conda environment

```
conda create -n env_name python=3.9
```
Change the env_name to a name for the conda environment.

## Activate newly created conda environment

```
conda activate env_name
```
This will make the `(env_name)` show up next to the command line on your terminal.

## Installing ichor core package

```python3
python3 -m pip install -e ichor_core_subpackage/
```

Now `ichor.core` has been installed. So for example to load in `GJF` class, you would do `from ichor.core.files import GJF`. 