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

