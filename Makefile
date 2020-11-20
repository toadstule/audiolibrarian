
.PHONY: clean
clean:
	rm -rf dist

.PHONY: format
format:
	black scripts/audiolibrarian .

.PHONY: requirements
requirements:
	python -m pip install -r requirements_base.txt

requirements.txt: requirements_base.txt requirements
	python -m pip freeze > $@

.PHONY: sdist
sdist: requirements
	python setup.py sdist

.PHONY: test
test:
	python -m unittest discover tests/

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
