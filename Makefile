.PHONY: help prepare-dev lint format docs test install update run

VENV_NAME?=venv
VENV_ACTIVATE=. $(VENV_NAME)/bin/activate
PYTHON=${VENV_NAME}/bin/python3

.DEFAULT: help
help:
	@echo "make help"
	@echo "       display this help message"
	@echo "make prepare-dev"
	@echo "       prepare development environment, use only once"
	@echo "make test"
	@echo "       run tests"
	@echo "make format"
	@echo "       run black and isort"
	@echo "make lint"
	@echo "       run pylint and mypy"
	@echo "make install"
	@echo "       install ichor via pip"
	@echo "make run"
	@echo "       run ichor"
	@echo "make docs"
	@echo "       build sphinx documentation and run doc tools"

prepare-dev:
	sudo apt-get -y install python3.6 python3-pip
	python3 -m pip install virtualenv
	make venv

# Requirements are in setup.py, so whenever setup.py is changed, re-run installation of dependencies.
venv: $(VENV_NAME)/bin/activate
$(VENV_NAME)/bin/activate: setup.py
	test -d $(VENV_NAME) || virtualenv -p python3 $(VENV_NAME)
	${PYTHON} -m pip install -U pip
	${PYTHON} -m pip install -e .
	touch $(VENV_NAME)/bin/activate

lint:
	pylint ichor/
	mypy ichor/

format:
	black ichor/
	isort ichor/

docs: venv
	$(VENV_ACTIVATE) && cd docs; make html
	${PYTHON} docs/src/make_globals_table.py
	${PYTHON} docs/src/make_tree_html.py

test: venv
	${PYTHON} -m unittest discover test/

install: venv
	${PYTHON} -m pip install -e .

run: venv
	${PYTHON} ichor3.py

update:
	git pull
