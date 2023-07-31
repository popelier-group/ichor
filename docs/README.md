# To generate docs

# Installing requirements

Install the requirements by doing 

```
pip install requirements.txt
```

Additionally, you will need to have the ichor packages installed. 

From the `docs` directory these are the sphinx commands to run to generate the .rst files automatically using `sphinx-apidoc`. Note that these `.rst` files do not actually contain the documentation but instead contains instructions on what to document. Then, when running `sphinx-build`, the `.rst` files are read and the Python code is executed to get the docstrings and make the documentation. Examples notebooks and other `.rst` pages to be displayed in the final documentation / website must be written manually.
:

```
sphinx-apidoc --implicit-namespaces --force -o source/ichor_core/ ../ichor_core_subpackage/ichor/

sphinx-apidoc --implicit-namespaces --force -o source/ichor_cli/ ../ichor_cli_subpackage/ichor/

sphinx-apidoc --implicit-namespaces --force -o source/ichor_hpc/ ../ichor_hpc_subpackage/ichor/

sphinx-build -a -E source/ build/
```

If you have `make` installed, you can run `make docs` which will run the
above commands automatically.
