# Project configuration
PYTHON = python3
UV = uv
VENV = .venv
SRC_DIR = src
LINT_DIRS = $(SRC_DIR)

# Default target
all: install

# Install dependencies
install:
	$(UV) sync

# Run the project
# usage: make run map=maps/easy1.txt
run:
	$(UV) run $(PYTHON) -m $(SRC_DIR) $(map)

# Debug mode
debug:
	$(UV) run $(PYTHON) -m pdb -m $(SRC_DIR) $(map)

# Linting
lint:
	$(UV) run flake8 $(LINT_DIRS)
	$(UV) run mypy $(LINT_DIRS) --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(UV) run flake8 $(LINT_DIRS)
	$(UV) run mypy $(LINT_DIRS) --strict

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf .pytest_cache

.PHONY: all install run debug lint lint-strict clean
