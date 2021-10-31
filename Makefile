#!/usr/bin/make

# These need to be at the top
PRESET_VARS := $(.VARIABLES)

PKG_FILES := scripts/audiolibrarian audiolibrarian
INSTALLED_PIP_PACKAGES := $(shell pip freeze)

.PHONY: all
all: sdist

.PHONY: check
check: CHECK = --check  # set this so "format" checks but doesn't change the files
check: lint test  ## Check the code.

.PHONY: clean
clean:  ## Clean up.
	rm -rf dist

.PHONY: distclean
distclean: clean venv-clean  ## Clean up all extra files.
	rm -rf MANIFEST .pytype .coverage htmlcov/ library/

.PHONY: format
format: requirements-dev  ## Format the code.
	black $(CHECK) $(PKG_FILES) tests
	isort $(CHECK) $(PKG_FILES) tests

.PHONY: help
help:  ## Display this help.
	@grep -h -E '^[a-zA-Z0-9._-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.PHONY: lint
lint: requirements requirements-dev format  ## Lint the code.
	pylint audiolibrarian
	pydocstyle $(PKG_FILES) tests
	pytype --jobs=auto --keep-going $(PKG_FILES) tests

.PHONY: requirements-base
requirements-base: requirements-base.txt  ## Install base requirements.
	python -m pip install --quiet --requirement requirements-base.txt

.PHONY: requirements-dev
requirements-dev: venv-check requirements-dev.txt  ## Install dev requirements.
	python -m pip install --quiet --requirement requirements-dev.txt

.PHONY: requirements
requirements: venv-check requirements.txt  ## Install requirements.
	python -m pip install --quiet --requirement requirements.txt

requirements.txt: requirements-base.txt  ## Make a new requirements file.
	make venv-clean
	make requirements-base
	python -m pip freeze > $@

.PHONY: sdist
sdist: requirements  ## Build distributable archive.
	python setup.py sdist

.PHONY: showvars
showvars:  ## Display variables available in the Makefile.
	$(foreach v, $(filter-out $(PRESET_VARS) PRESET_VARS,$(.VARIABLES)), $(info $(v) = $($(v))))
	$(info)

.PHONY: test
test:  ## Run unit tests.
	python -X dev -m unittest discover tests/

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
venv-check:  # Verify that we are in a virtual environment.
ifndef VIRTUAL_ENV
ifndef BITBUCKET_WORKSPACE
	$(error this should only be executed in a Python virtual environment)
endif
endif

.PHONY: venv-clean
venv-clean: venv-check  ## Remove all packages from the virtual environment
ifdef INSTALLED_PIP_PACKAGES
	-@pip uninstall --quiet --yes $(INSTALLED_PIP_PACKAGES)
endif
