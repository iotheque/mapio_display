.PHONY: clean clean-test clean-pyc clean-build docs help dist wheel sdist
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	# Note: the "$$" is here because it is rendered by make, and a single "$" is passed to Python
	match = re.match(r'^([a-zA-Z0-9\/_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test clean-docs ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage*
	rm -f coverage.xml
	rm -fr htmlcov/
	rm -fr .pytest_cache

clean-docs: ## remove documentation artifacts
	rm -rf docs/

format: ## format the code using black
	tox -e isort,black

lint/flake8: ## check style with flake8
	tox -e flake8

lint/black: ## check style with black
	tox -e black_check

lint/mypy: ## check type hints with mypy
	tox -e mypy

lint/bandit: ## check for vulnerabilities with bandit
	tox -e bandit

lint/isort: ## check import order with isort
	tox -e isort_check

lint: ## check formatting and linting
	tox -p -e flake8,mypy,bandit,black_check,isort_check

test: ## run the test suite against all the local python version
	tox -e py3

test-all: ## run the test suite against all the python versions
	tox -p -e py36,py37,py38,py39,py310

coverage: ## run code coverage analysis against the local Python3 version
	tox -e py3,coverage

coverage-all: ## run code coverage analysis against all the Python versions
	tox -p -e py36,py37,py38,py39,py310
	tox -e coverage

docs: clean-docs ## generate code documentation with pdoc
	tox -e docs

live-docs: clean-docs ## start an HTTP server that serves the live documentation
	tox -e live-docs

dist: ## builds source and wheel distributions
	tox -e build

sdist: ## builds source distribution
	tox -e build -- --sdist

wheel: ## builds wheel distribution
	tox -e build -- --wheel

build-docker: wheel ## builds a Docker image that can run the package, using Python 3.9.10
	docker build -t mapio_display:latest .

install: clean ## install the package to the active Python's site-packages
	pip install .

install-dev: clean ## install the package in dev mode, and the required dev dependencies
	pip install -r requirements_dev.txt

bump-patch: ## bumps the package patch version number
	tox -e bump patch

bump-minor: ## bumps the package minor version number
	tox -e bump minor

bump-major: ## bumps the package major version number
	tox -e bump major


update-template: ## updates the repository to the latest version of the template using cruft
	tox -e cruft
