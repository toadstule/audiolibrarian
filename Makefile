#!/usr/bin/make

# These need to be at the top
PRESET_VARS := $(.VARIABLES)

# Project variables
MD_FILES        := $(shell find . -name '*.md' | grep -v "/.venv/" | grep -v "/dist/")
PROJECT_NAME    := $(shell grep -e '^name =' pyproject.toml | cut -d'"' -f2)
PY_FILES        := $(shell find . -name '*.py' | grep -v "/.venv/" | grep -v "/dist/")
PYTHON_VERSION_ := $(shell cat .python-version)
VERSION         := $(shell grep -e '^version =' pyproject.toml | cut -d'"' -f2)
WHEEL           := dist/$(PROJECT_NAME)-$(VERSION)-py3-none-any.whl

# Tool variables
BROWSER  := $(shell command -v chromium || command -v google-chrome-stable || command -v firefox )
PYTHON   := $(shell command -v python$(PYTHON_VERSION_))
UV       := $(shell command -v uv)
COVERAGE := $(UV) run coverage
MDLINT   := $(UV) run pymarkdownlnt
MYPY     := $(UV) run mypy
PIP      := $(UV) pip
PYTEST   := $(UV) run pytest
RUFF     := $(UV) run ruff

# Verify that we have the required tools.
ifndef UV
$(error "uv is not installed. Please install it with your package manager.")
endif


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
	@rm -rf htmlcov .coverage
	@rm -rf .pytype
	@rm -rf .ruff_cache .mypy_cache
	@rm -rf site .cache .mkdocs
	@$(UV) clean
	@rm -rf dist

.PHONY: docs
docs: docs-build  ## Build and serve the documentation
	@mkdocs serve

.PHONY: docs-build
docs-build: dep  ## Build the documentation
	@mkdocs build --clean

.PHONY: docs-deploy
docs-deploy: dep  ## Deploy the documentation to GitHub Pages
	@mkdocs gh-deploy --force

.PHONY: dep
dep: uv.lock  ## Install dependencies.
	@$(UV) sync --locked --all-extras --dev

.PHONY: dep-upgrade
dep-upgrade:  ## Upgrade dependencies.
	$(UV) lock --upgrade

.PHONY: format
format: dep  ## Format the code; sort the imports.
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
	@$(MDLINT) scan $(MD_FILES)

.PHONY: publish
publish: $(WHEEL)  ## Publish the package to PyPI.
	@$(UV) publish --publish-url https://pypi.jibson.com --token none

.PHONY: showvars
showvars:  ## Display variables available in the Makefile.
	$(foreach v, $(filter-out $(PRESET_VARS) PRESET_VARS,$(.VARIABLES)), $(info $(v) = $($(v))))

.PHONY: test
test: dep  ## Run unit tests.
	$(PYTEST) --verbose tests

.PHONY: test-coverage
test-coverage:  ## Run unit tests and generate a coverage report.
	rm -rf htmlconv
	coverage run -m pytest tests/
	coverage html
	$(BROWSER) htmlcov/index.html

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

uv.lock: pyproject.toml
	@$(UV) lock

$(WHEEL): $(PY_FILES) pyproject.toml uv.lock dep
	@$(UV) build
