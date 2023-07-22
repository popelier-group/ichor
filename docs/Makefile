# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build
SPHINXAPIDOC  ?= sphinx-apidoc

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
# %: Makefile
# 	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

%: docs
	@$(SPHINXAPIDOC) --implicit-namespaces -d 1 --force -o source/ichor_core/ ../ichor_core_subpackage/ichor/
	@$(SPHINXAPIDOC) --implicit-namespaces -d 1 --force -o source/ichor_cli/ ../ichor_cli_subpackage/ichor/
	@$(SPHINXAPIDOC) --implicit-namespaces -d 1 --force -o source/ichor_hpc/ ../ichor_hpc_subpackage/ichor/

	rm -f source/ichor_core/ichor.rst
	rm -f source/ichor_core/modules.rst
	rm -f source/ichor_hpc/ichor.rst
	rm -f source/ichor_hpc/modules.rst
	rm -f source/ichor_cli/ichor.rst
	rm -f source/ichor_cli/modules.rst

	@$(SPHINXBUILD) -a -E "$(SOURCEDIR)" "$(BUILDDIR)"

%: quick
	@$(SPHINXAPIDOC) --implicit-namespaces -d 1 -o source/ichor_core/ ../ichor_core_subpackage/ichor/
	@$(SPHINXAPIDOC) --implicit-namespaces -d 1 -o source/ichor_cli/ ../ichor_cli_subpackage/ichor/
	@$(SPHINXAPIDOC) --implicit-namespaces -d 1 -o source/ichor_hpc/ ../ichor_hpc_subpackage/ichor/

	rm -f source/ichor_core/ichor.rst
	rm -f source/ichor_core/modules.rst
	rm -f source/ichor_hpc/ichor.rst
	rm -f source/ichor_hpc/modules.rst
	rm -f source/ichor_cli/ichor.rst
	rm -f source/ichor_cli/modules.rst

	@$(SPHINXBUILD) "$(SOURCEDIR)" "$(BUILDDIR)"
