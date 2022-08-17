# Deep Dive Documentation

- [Formatting the code](#formatting-the-code)
- [Linting the code](#linting-the-code)
- [Running the test suite](#running-the-test-suite)
- [Generating code coverage](#generating-code-coverage)
- [Increasing version number](#increasing-version-number)
  - [You are starting work on a new development version](#you-are-starting-work-on-a-new-development-version)
  - [You are bumping a development version](#you-are-bumping-a-development-version)
  - [You are releasing a development version](#you-are-releasing-a-development-version)
- [Building and distributing](#building-and-distributing)
- [Dependency management](#dependency-management)
  - [Runtime dependencies](#runtime-dependencies)
  - [Development dependencies](#development-dependencies)
- [Update to the latest template version](#update-to-the-latest-template-version)

Most of the commands described in the following sections can be found in the `Makefile` of this project. Run `make help` to get the list of all possible commands and their description.

## Formatting the code

**TL;DR**: `make format`

The code of this project is formatted using [black](https://black.readthedocs.io) and [isort](https://pycqa.github.io/isort) in order to avoid any useless negotiations revolving around formatting preferences.

To format your code, you can either:

- run them from `tox` with `make format`
- install `black` and `isort` on your machine, and configure your IDE to use them
- install `black` `isort` on your machine, and manually run them with:
  - `black src/ tests/`
  - `isort src/ tests/`

## Linting the code

**TL;DR**: `make lint`

The code of this project is linted using 3 tools:

- [flake8](https://flake8.pycqa.org) checks the code for syntactical correctness
- [mypy](http://mypy-lang.org/) checks the code for type correctness
- [bandit](https://bandit.readthedocs.io) checks the code for security vulnerabilities

To run these linters, you can:

- run them with `tox` using `make lint`
- install them on your machine, and configure your IDE to use them
- install them on your machine, and run them manually with:
  - `flake8 src/ tests/`
  - `mypy src/ tests/`
  - `bandit src/ tests/`

**Note**: these linters are also part of the CI

## Running the test suite

**TL;DR**: `make test`

The `tox` configuration of this project allows you to test your code on 5 different versions of Python (3.6, 3.7, 3.8, 3.9, and 3.10). If you want to test all 5 on your machine, you will need to first install them. You can look at [pyenv](https://github.com/pyenv/pyenv) to cleanly manage multiple versions of Python. Otherwise, you can decide to test only against the Python version you have installed locally.

To run the tests against your main Python3 version:

``` sh
make test
```

To run the test suite against all 5 Python versions, run:

``` sh
make test-all
```

To run the test suite with a specific list of Python versions, run:

``` sh
tox -p -e $VERSIONS_LIST
```

where $VERSIONS_LIST is a comma-separated list of the Python versions to test against. For example, to test against Python 3.6 and 3.8:

``` sh
tox -p -e py36,py38
```

**Note**: the `-p` flag is used to run the multiple test environments in parallel.

## Generating code coverage

**TL;DR**: `make coverage`

A coverage report of the tests of this project can be generated with the following command:

``` sh
make coverage
```

This will run the test suite with your main Python3 version, print a coverage report in your terminal, and generate an HTML version in `htmlcov/`

You can generate this report outside of `tox`, with the command:

``` sh
coverage run -m pytest && coverage combine && coverage report && coverage html
```

You can also generate the coverage report for all Python versions at once with the command:

``` sh
make coverage-all
```

## Increasing version number

**TL;DR**: `make bump-[major|minor|patch]` on a clean git repository.

The version number of this project can be upgraded using `bump2version`, already included in the `requirements_dev.txt` file, or using `tox`. When used, this tool will edit the following files to update their versions, create a new commit with these edits, and tag it with the new version number.

- `src/mapio_display/VERSION`
- `README.md`
- `setup.cfg`

The version number is always in the format `X.Y.Z`, with :

- `X` is the major version number
- `Y` is the minor version number
- `Z` is the patch version number

To use this tool, make sure that your Git repo is clean, and in the state you wish to publish your new version with. Then, update your version number, using semantic versioning:

- if the changes since the last version are just bugfixes, documentation improvement, any other "chore" commit, update the `patch` version number, with `make bump-patch`
- if your changes introduce new features, update the `minor` version with `make bump-minor`
- if your changes include a breaking change, update the `major` version with `make bump-major`

## Building and distributing

When you want to distribute the code of this repo, you can either:

- manually build the `sdist` and `wheel` with `make dist`
- manually build the `sdist` with `make sdist`
- manually build the `wheel` with `make wheel`
- run the `build` CI stage of the repo

These commands will generate `.tar.gz` or `.whl` archives. These files can be installed with `pip install $FILENAME` on any target machine that supports their requirements.

## Dependency management

The dependencies of this project are split in two:

- The runtime dependencies, that need to be installed in order for the project to be functional
- The development dependencies, that only need to be present when editing, testing, or building this project

### Runtime dependencies

The runtime dependencies are listed in the `setup.cfg` file, in the `[options]` section, under the `install_requires` label. Each dependency should be listed on a separate line, with a version number attached to it. When installing the package with `pip`, `setuptools` will automatically parse this config file, and install the dependencies.

**Note**: the version number you specify can be either strict (e.g. `==4.2.1`), loose (e.g. `~=4.2`), or bounded (e.g. `>=4.2`)

### Development dependencies

These dependencies are listed in `requirements_dev.txt`, and should be installed on your dev machine, preferably in a [virtualenv](https://docs.python.org/3/library/venv.html).

Most of the libraries listed in the dependency file are also duplicated in the `tox.ini` file. This file contains the configuration of all the `tox` environments. Each environment is designed to only install the packages it needs (e.g. the `black` environment will not install `pytest`) in order to speed up their execution. It is therefore important to make sure you update the package versions in `tox.ini` if you update them in `requirements_dev.txt`, otherwise you risk encountering some problems when running inside `tox`.

## Update to the latest template version

**TL;DR**: `make update-template`

If you have generated this project with `cruft`, or linked it to this template afterwards, you can reuse this tool to fetch and apply the latest template updates.
This is done with the `make update-template` command, which will invoke `cruft` through `tox`, and apply all the changes done to the branch configured in your `.cruft.json` file
(`master` by default) since the last update (which hash is also stored in `.cruft.json`). These changes will be immediately staged, and the `.cruft.json` fiel will be updated to
store the hash of the latest template commit used.
