# Project configuration
PYTHON = python3
PIP = PYTHONPATH=. uv
VENV = .venv
SRC_DIR = src
LINT_DIRS = $(SRC_DIR)

# Default target
all: install

# Install dependencies
install:
	$(PIP) venv $(VENV)
	$(PIP) sync

# Run the project
# usage: make run map=maps/easy1.txt
run:
	$(PIP) run $(SRC_DIR) $(map)

# Debug mode
debug:
	$(VENV)/bin/$(PYTHON) -m pdb $(SRC_DIR)/main.py $(map)

# Linting
lint:
	$(VENV)/bin/mypy $(LINT_DIRS) --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
	$(VENV)/bin/flake8 $(LINT_DIRS)

lint-strict:
	$(VENV)/bin/mypy $(LINT_DIRS) --strict
	$(VENV)/bin/flake8 $(LINT_DIRS)

# Cleanup
clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf .pytest_cache

.PHONY: all install run debug lint lint-strict clean
