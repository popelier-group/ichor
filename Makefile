typehint:
	mypy ichor/

format:
	black ichor/
	isort ichor/

docs:
	python3 docs/src/make_globals_table.py
	python3 docs/src/make_tree_html.py

test:
	python3 -m pytest

install:
	python3 -m pip install -e .

update:
	git pull

.PHONY: typehint format docs test install update
