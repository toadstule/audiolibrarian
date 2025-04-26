#!/usr/bin/make

# These need to be at the top
PRESET_VARS := $(.VARIABLES)

# Project variables
PROJECT_NAME    := $(shell grep -e '^name =' pyproject.toml | cut -d'"' -f2)
PY_FILES        := $(shell find . -name '*.py' | grep -v "/.venv/" | grep -v "/dist/")
PYTHON_VERSION_ := $(shell cat .python-version)
VERSION         := $(shell grep -e '^version =' pyproject.toml | cut -d'"' -f2)
WHEEL           := dist/$(PROJECT_NAME)-$(VERSION)-py3-none-any.whl

# Tool variables
PYTHON := $(shell which python$(PYTHON_VERSION_))
MYPY   := $(PYTHON) -m mypy
PYTEST := $(PYTHON) -m pytest
RUFF   := $(PYTHON) -m ruff
UV     := $(shell command -v uv 2> /dev/null)
PIP    := $(UV) pip

# Parse dependencies from pyproject.toml
DEPS     := $(shell sed -n '/^\s*dependencies\s*=\s*\[/,/^\s*]/p' pyproject.toml | grep -vE '^\s*dependencies\s*=\s*\[|^\s*\]' | sed -E 's/[",]//g' | sed -E 's/[<>=!~].*//' | grep -vE '^\s*$$' | xargs)
DEV_DEPS := $(shell sed -n '/^\s*dev\s*=\s*\[/,/^\s*]/p' pyproject.toml | grep -vE '^\s*dev\s*=\s*\[|^\s*\]' | sed -E 's/[",]//g' | sed -E 's/[<>=!~].*//' | grep -vE '^\s*$$' | xargs)

.PHONY: all
all: build

.PHONY: build
build: $(WHEEL)  ## Build the package.

.PHONY: check
check: lint test  ## Check the code.

.PHONY: clean
clean:  ## Clean up.
	@find . -name "__pycache__" | grep -v "/.venv/" | xargs rm -rf
	@rm -rf .pytest_cache tests/.pytest_cache
	@rm -rf .pytype
	@$(UV) clean
	@rm -rf dist

.PHONY: dep
dep:  ## Install dependencies.
	@$(UV) sync

.PHONY: dep-upgrade
dep-upgrade:  # Update (remove and re-install) dependencies.
	$(UV) remove $(DEPS)
	$(UV) remove --dev $(DEV_DEPS)
	$(UV) add $(DEPS)
	$(UV) add --dev $(DEV_DEPS)
	$(UV) lock

.PHONY: format
format:  ## Format the code; sort the imports.
	@$(RUFF) format $(PY_FILES)
	@$(RUFF) check --fix --select I $(PY_FILES)

.PHONY: help
help:  ## Display this help.
	@grep -h -E '^[a-zA-Z0-9._-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: venv-check $(WHEEL)  ## Install the package (locally).
	@$(PIP) install --editable .

.PHONY: lint
lint: format  ## Lint the code.
	@$(RUFF) format --check src
	@$(RUFF) check src
	@$(MYPY) --non-interactive $(PY_FILES)


.PHONY: publish
publish: $(WHEEL)  ## Publish the package to PyPI.
	@$(UV) publish --publish-url https://pypi.jibson.com --token none


.PHONY: showvars
showvars:  ## Display variables available in the Makefile.
	$(foreach v, $(filter-out $(PRESET_VARS) PRESET_VARS,$(.VARIABLES)), $(info $(v) = $($(v))))

.PHONY: test
test:  ## Run unit tests.
	$(PYTEST) --verbose tests

.PHONY: test-coverage
test-coverage:  ## Run unit tests and generate a coverage report.
	rm -rf htmlconv
	coverage run -m unittest discover tests/
	coverage html
	chromium htmlcov/index.html

.PHONY: test-external
test-external:  ## Run unit tests -- including external tests.
	EXTERNAL_TESTS=1 make test

.PHONY: test-external-coverage
test-external-coverage:  ## Run unit tests -- including external tests -- and generate a coverage report.
	EXTERNAL_TESTS=1 make test-coverage

.PHONY: venv-check
venv-check:  # Verify that we are in a virtual environment (or in a Python container).
ifndef VIRTUAL_ENV
ifndef PYTHON_VERSION
	$(error this should only be executed in a Python virtual environment)
endif
endif

$(WHEEL): $(PY_FILES) pyproject.toml uv.lock dep
	@$(UV) build
