PKG_FILES := scripts/audiolibrarian audiolibrarian

.PHONY: clean
clean:
	rm -rf dist

.PHONY: format
format:
	black $(PKG_FILES) tests
	isort $(PKG_FILES) tests

.PHONY: lint
lint: format
	pylint audiolibrarian
	pydocstyle $(PKG_FILES) tests
	pytype --jobs=auto --keep-going $(PKG_FILES) tests

.PHONY: requirements
requirements:
	python -m pip install -r requirements-base.txt

requirements.txt: requirements-base.txt requirements
	python -m pip freeze > $@

.PHONY: sdist
sdist: requirements
	python setup.py sdist

.PHONY: test
test:
	python -X dev -m unittest discover tests/

.PHONY: test-coverage
test-coverage:
	rm -rf htmlconv
	coverage run -m unittest discover tests/
	coverage html
	chromium htmlcov/index.html

.PHONY: test-external
test-external:
	EXTERNAL_TESTS=1 make test

.PHONY: test-external-coverage
test-external-coverage:
	EXTERNAL_TESTS=1 make test-coverage
