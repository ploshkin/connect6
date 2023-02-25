.PHONY: test

default: test

format:
	black --line-length=88 ./

clean: clean-build clean-pyc clean-pycache

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

clean-pycache:
	find . -name '__pycache__' -exec rm -rf {} +

test:
	PYTHONPATH=./ pytest tests/
