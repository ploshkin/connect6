.PHONY: lint mypy clean clean-build clean-pyc test test-all pre-commit

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8, black & isort"
	@echo "mypy - check types with mypy"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "pre-commit - run pre-commit hooks on all files"

lint:
	tox -e lint

mypy:
	tox -e type

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

test:
	tox -e test

test-all:
	tox

pre-commit:
	pre-commit run --all-files
