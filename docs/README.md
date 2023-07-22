# To generate docs

From the `docs` directory these are the sphinx commands to run to generate the .rst files and make the docs
The default docs don't look too good, so will update them in the future
:

```
sphinx-apidoc --implicit-namespaces --force -o source/ichor_core/ ../ichor_core_subpackage/ichor/

sphinx-apidoc --implicit-namespaces --force -o source/ichor_cli/ ../ichor_cli_subpackage/ichor/

sphinx-apidoc --implicit-namespaces --force -o source/ichor_hpc/ ../ichor_hpc_subpackage/ichor/

sphinx-build -a -E source/ build/
```

If you have `make` installed, you can run `make docs` which will run the
above commands automatically.
