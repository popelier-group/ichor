typehint:
	mypy ichor/

format:
	black ichor/
	isort ichor/

.PHONY: typehint format
