# Quickstart

This file provides a quick documentation of the most useful features of this template. For more detailed documentation, see the [Deep Dive documentation](./Deep-dive.md).

- [How do I...](#how-do-i)
  - [...setup my development environment?](#setup-my-development-environment)
  - [...test my code?](#test-my-code)
  - [...format my code?](#format-my-code)
  - [...lint my code?](#lint-my-code)
  - [...generate test coverage?](#generate-test-coverage)
  - [...bump the version number of my package?](#bump-the-version-number-of-my-package)
  - [...generate a distribution archive?](#generate-a-distribution-archive)
  - [...build a Docker image that runs my package?](#build-a-docker-image-that-runs-my-package)
  - [...generate the API documentation?](#generate-the-api-documentation)
  - [...update the project to the latest version of the template?](#update-the-project-to-the-latest-version-of-the-template)

## How do I...

### ...setup my development environment?

These instructions assume that you already have a working development version of Python3 installed on your machine.
If this is not the case, start by doing installing one. One recommended method is by using [pyenv](https://github.com/pyenv/pyenv),
a tool that allows you to easily manage the versions of Python you have installed on your machine.

You can then run the following commands to setup your environment:

``` sh
# Clone this repo
git clone https://github.com/pcurt/mapio_display
# Move into the directory
cd mapio_display
# Create a virtualenv
python3 -m venv venv
# Activate the virtualenv
source ./venv/bin/activate
# Install the dev dependencies in your environment
make install-dev
# Check that everything worked as expected by running the linters, test suite, and building the package
# NOTE: This can take a couple of minutes
make lint test docs dist build-docker
```

You now have a `virtualenv` with all the development dependencies installed, as well as your package installed in development mode.

### ...test my code?

`make test`

This will run the test suite located in the `tests/` directory against the available Python3 install, using `tox`.

### ...format my code?

`make format`

This will run `black` and `isort` on the `src/` and `tests/` directories, formatting your code properly.

### ...lint my code?

`make lint`

This will call the 3 linters (`mypy`, `flake8`, and `bandit`) and the 2 formatters in check-only mode, and tell you if your code passes them.

### ...generate test coverage?

`make coverage`

This will run the test suite against the available Python3 install using `tox`, and generate
a code coverage report in the `htmlcov` directory.

### ...bump the version number of my package?

`make bump-[major|minor|patch]` on a clean `git` repository

This will increase the corresponding version fragment of your project, following the rules of
semantic versioning.

For example:

- `bump-major`: 1.2.4 --> 2.0.0
- `bump-minor`: 1.2.4 --> 1.3.0
- `bump-patch`: 1.2.4 --> 1.2.5

**Note**: if you generated this template to use the `rcX` suffix in the version number, see the [Deep Dive documentation](./Deep-dive.md) to learn how to use it.

### ...generate a distribution archive?

`make dist`

This will build a `.tar.gz` and a `.whl` distribution files, that can then be installed on a
target machine with `pip install $FILENAME`.

### ...build a Docker image that runs my package?

`make build-docker`

This will build a `.whl` distribution, and use it to build a minimal Docker image, tagged `mapio_display:latest`, that runs it.

### ...generate the API documentation?

`make docs`

This will parse all the docstrings of the package, and generate an HTML documentation that includes them, as well as all the files in the `readme/` directory.

### ...update the project to the latest version of the template?

`make update-template`

This will call `cruft`, which will generate and apply a `diff` of all the changes done to the template since you last updated this
project. Your local `git` repo needs to be clean in order for this to work.
