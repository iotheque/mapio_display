# mapio_display

MAPIO display source code

- [Development Quickstart](#development-quickstart)
- [Installation](#installation)
  - [From a release archive](#from-a-release-archive)
  - [From sources](#from-sources)
- [Usage](#usage)

## Development Quickstart

A quickstart guide/cheatsheet is [available here](./readme/Quickstart.md), that lists the useful commands when developing this package.

## Installation

The two following methods will install this project as an executable callable directly from your terminal.

Note that you should ideally run these `pip` commands in an active [virtualenv](https://docs.python.org/3/library/venv.html), and not in your system Python install.

### From a release archive

To install mapio_display, download the latest release archive fom Github, and run this command in your terminal:

``` sh
pip install mapio_display-1.0.0-py3-none-any.whl
# or
pip install mapio_display-1.0.0.tar.gz
```

### From sources

The sources for mapio_display can be downloaded from the [Github repo](https://github.com/pcurt/mapio_display).

Start by cloning the repository:

``` sh
git clone git@github.com:pcurt/mapio_display.git
```

Then enter the cloned directory (with `cd mapio_display/`), and install the project with:

``` sh
pip install .
```

## Usage

Describe here how to use this Python package: CLI options and flags, API when imported by another package, etc.
