<h1 align="center">OpenLane 2.0</h1>
<p align="center">
    <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License: Apache 2.0"/></a>
    <a href="https://openlane.readthedocs.io/"><img src="https://readthedocs.org/projects/openlane/badge/?version=latest" alt="Documentation Build Status Badge"/></a>
    <a href="https://invite.skywater.tools"><img src="https://img.shields.io/badge/Community-Open%20Source%20Silicon%20Slack-ff69b4?logo=slack" alt="Invite to the Open Source Silicon Slack"/></a>
    <a href="https://www.python.org"><img src="https://img.shields.io/badge/Python-3.8-3776AB.svg?style=flat&logo=python&logoColor=white" alt="Python 3.8 or higher" /></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code Style: black"/></a>
    <a href="https://mypy-lang.org/"><img src="https://www.mypy-lang.org/static/mypy_badge.svg" alt="Checked with mypy"/></a>
</p>

OpenLane is an automated RTL to GDSII flow based on several components including OpenROAD, Yosys, Magic, Netgen, CVC, SPEF-Extractor, KLayout and a number of custom scripts for design exploration and optimization. The flow performs all ASIC implementation steps from RTL all the way down to GDSII.

## Installation
### Binary Dependencies
You'll need the following:
* The **absolute latest** (HEAD of master) Yosys from https://github.com/YosysHQ/Yosys
* A reasonably modern version of OpenROAD from https://github.com/The-OpenROAD-Project/OpenROAD
* A reasonably modern version of Magic from https://github.com/RTimothyEdwards/Magic
* Python **3.8** or higher with PIP, Venv and Python-Tk

### Installing on Ubuntu
```sh
sudo apt-get install python3 python3-pip python3-venv python3-tk libxz
```

### Python Dependencies
For now, simply type `make venv` to create a virtual environment with all the
Python dependencies installed. To activate the virtual environment, type
`source ./venv/bin/activate` in your terminal.

## Usage
In the root folder of the repository, you may invoke:

```sh
python3 -m openlane --pdk-root <path/to/pdk> </path/to/config.json>
```

To start with, you can try:

```sh
python3 -m openlane --pdk-root $HOME/.volare ./designs/spm/config.json
```