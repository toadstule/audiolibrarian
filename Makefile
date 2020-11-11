
.PHONY: clean
clean:
	rm -rf dist

.PHONY: format
format:
	black scripts/audiolibrarian .

.PHONY: requirements
requirements:
	python -m pip install -r requirements.txt

#requirements.txt: requirements_base.txt requirements
#	python -m pip freeze > $@

.PHONY: sdist
sdist: requirements
	python setup.py sdist

.PHONY: test
test:
	python -m unittest discover tests/
