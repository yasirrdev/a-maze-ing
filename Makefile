PYTHON = python3
PIP = $(PYTHON) -m pip
MAIN = a_maze_ing.py
CONFIG = config/default.txt

FLAKE8 = flake8 .
MYPY = mypy . --warn-return-any --warn-unused-ignores \
	--ignore-missing-imports --disallow-untyped-defs \
	--check-untyped-defs
MYPY_STRICT = mypy . --strict

.PHONY: install run debug clean lint lint-strict re

install:
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) $(MAIN) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(MAIN) $(CONFIG)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf output

lint:
	$(FLAKE8)
	$(MYPY)

lint-strict:
	$(FLAKE8)
	$(MYPY_STRICT)

re: clean run
