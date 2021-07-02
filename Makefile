#!/usr/bin/make

# These need to be at the top
PRESET_VARS := $(.VARIABLES)

PKG_FILES := scripts/audiolibrarian audiolibrarian

.PHONY: all
all: sdist

.PHONY: check
check: CHECK = --check  # set this so "format" checks but doesn't change the files
check: lint test  ## Check the code.

.PHONY: clean
clean:  ## Clean up.
	rm -rf dist

.PHONY: distclean
distclean: clean  ## Clean up all extra files.
	rm -rf MANIFEST .pytype .coverage htmlcov/ library/

.PHONY: format
format:  ## Format the code.
	black $(CHECK) $(PKG_FILES) tests
	isort $(CHECK) $(PKG_FILES) tests

.PHONY: help
help:  ## Display this help.
	@grep -h -E '^[a-zA-Z0-9._-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.PHONY: lint
lint: format  ## Lint the code.
	pylint audiolibrarian
	pydocstyle $(PKG_FILES) tests
	pytype --jobs=auto --keep-going $(PKG_FILES) tests

.PHONY: requirements
requirements:  ## Install requirements.
	python -m pip install -r requirements-base.txt

requirements.txt: requirements-base.txt requirements  ## Make a new requirements file.
	python -m pip freeze > $@

.PHONY: sdist
sdist: requirements  ## Build distributable archive.
	python setup.py sdist

.PHONY: showvars
showvars:  ## Display variables available in the Makefile.
	$(foreach v, $(filter-out $(PRESET_VARS) PRESET_VARS,$(.VARIABLES)), $(info $(v) = $($(v))))
	@echo

.PHONY: test
test: lint  ## Run unit tests.
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
