<h1 align="center">OpenLane 2.0</h1>
<p align="center">
    <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License: Apache 2.0"/></a>
    <a href="https://openlane.readthedocs.io/"><img src="https://readthedocs.org/projects/openlane/badge/?version=latest" alt="Documentation Build Status Badge"/></a>
    <a href="https://invite.skywater.tools"><img src="https://img.shields.io/badge/Community-Open%20Source%20Silicon%20Slack-ff69b4?logo=slack" alt="Invite to the Open Source Silicon Slack"/></a>
    <a href="https://www.python.org"><img src="https://img.shields.io/badge/Python-3.8-3776AB.svg?style=flat&logo=python&logoColor=white" alt="Python 3.8 or higher" /></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code Style: black"/></a>
    <a href="https://mypy-lang.org/"><img src="https://www.mypy-lang.org/static/mypy_badge.svg" alt="Checked with mypy"/></a>
</p>

OpenLane is a RTL to GDSII infrastructure library based on several components including OpenROAD, Yosys, Magic, Netgen, CVC, SPEF-Extractor, KLayout and a number of custom scripts for design exploration and optimization. A reference flow performs all ASIC implementation steps from RTL all the way down to GDSII.

## Installation
### Binary Dependencies
You'll need the following:
* Yosys 0.23+ (preferably 0.26+) from https://github.com/YosysHQ/Yosys
* A reasonably modern version of OpenROAD from https://github.com/The-OpenROAD-Project/OpenROAD
* A reasonably modern version of Magic from https://github.com/RTimothyEdwards/Magic
* A reasonably modern version of Netgen from https://github.com/RTimothyEdwards/netgen
* Python **3.8** or higher with PIP, Venv and Python-Tk

### Nix
* Install [Nix](https://nixos.org/download.html). \[Package manager. Takes around 3 minutes.\]
    * On Linux, invoke `sh <(curl -L https://nixos.org/nix/install) --daemon` and follow the instructions.
    * On Mac, invoke `sh <(curl -L https://nixos.org/nix/install) --daemon` and follow the instructions.
* Install [Cachix](https://cachix.org). \[Binary caching tool. Takes around a minute.\]
    * `nix-env -iA cachix -f https://cachix.org/api/v1/install`
* Set up the [OpenLane Cachix](https://app.cachix.org/cache/openlane) \[Package manager. Takes around a minute.\]
    * `cachix use openlane`
    * You may see a message about your user not being trusted. In that case, it will print out a command. Please run that command then **re-run** `cachix use openlane`.

That's it. Whenever you want to use OpenLane, `nix-shell` in the repository root directory and you'll have a full OpenLane environment. The first time might take around 10 minutes while binaries are pulled from the cache.

### Other Methods
You'll need to compile the above tools. We're planning to support Conda down the line.

To set up the Python deps, simply type `make venv` to create a virtual environment 
with all the Python dependencies installed. To activate the virtual environment,
type `source ./venv/bin/activate` in your terminal.

## Usage
In the root folder of the repository with the VENV activated, you may invoke:

```sh
openlane --pdk-root <path/to/pdk> </path/to/config.json>
```

To start with, you can try:

```sh
openlane --pdk-root $HOME/.volare ./designs/spm/config.json
```