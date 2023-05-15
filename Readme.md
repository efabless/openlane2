> Efabless OpenLane 2 is in early access and all APIs are, presently, highly unstable and subject to change without notice.
>
> If you *don't* know why you're here, you're probably looking for the stable version of OpenLane at https://github.com/The-OpenROAD-Project/OpenLane.

<h1 align="center">OpenLane</h1>
<p align="center">
    <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License: Apache 2.0"/></a>
    <a href="https://www.python.org"><img src="https://img.shields.io/badge/Python-3.8-3776AB.svg?style=flat&logo=python&logoColor=white" alt="Python 3.8 or higher" /></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code Style: black"/></a>
    <a href="https://mypy-lang.org/"><img src="https://www.mypy-lang.org/static/mypy_badge.svg" alt="Checked with mypy"/></a>
    <a href="https://nixos.org/"><img src="https://img.shields.io/static/v1?logo=nixos&logoColor=white&label=&message=Built%20with%20Nix&color=41439a" alt="Built with Nix"/></a>
</p>
<p align="center">
    <a href="https://openlane2.readthedocs.io/"><img src="https://readthedocs.org/projects/openlane2/badge/?version=latest" alt="Documentation Build Status Badge"/></a>
    <a href="https://invite.skywater.tools"><img src="https://img.shields.io/badge/Community-Open%20Source%20Silicon%20Slack-ff69b4?logo=slack" alt="Invite to the Open Source Silicon Slack"/></a>
</p>

OpenLane is a RTL to GDSII infrastructure library based on several components including OpenROAD, Yosys, Magic, Netgen, CVC, KLayout and a number of custom scripts for design exploration and optimization. A reference flow performs all ASIC implementation steps from RTL all the way down to GDSII.

You can find the documentation [here](https://openlane2.readthedocs.io/) to get started.

```python
from openlane import Flow

Classic = Flow.get("Classic")

flow = Classic.init_with_config(
    {
        "PDK": "sky130A",
        "DESIGN_NAME": "spm",
        "VERILOG_FILES": ["./src/spm.v"],
        "CLOCK_PORT": "clk",
        "CLOCK_PERIOD": 10,
    },
    design_dir=".",
)

flow.start()
```


## Installation
### Binary Dependencies
You'll need the following:
* Python **3.8** or higher with PIP, Venv and Tkinter
* Yosys 0.23+ (preferably 0.26+) from https://github.com/YosysHQ/Yosys
* A reasonably modern version of OpenROAD from https://github.com/The-OpenROAD-Project/OpenROAD
* A reasonably modern version of Magic from https://github.com/RTimothyEdwards/Magic
* A reasonably modern version of Netgen from https://github.com/RTimothyEdwards/netgen
* KLayout 0.28.5+ from https://github.com/KLayout/klayout

### Docker
Works for Windows, macOS and Linux. Easier to set up, but less integrated with your filesystem. Recommended for general users.

See [Docker-based installation](https://openlane2.readthedocs.io/en/latest/getting_started/docker_installation/index.html) in the docs.

Do note you'll need to add `--dockerized` to most CLI invocations of OpenLane.

### Nix
Works for macOS and Linux. A bit more complex to set up, but more integrated with your filesystem and overall less upload and download deltas.

See [Nix-based installation](https://openlane2.readthedocs.io/en/latest/getting_started/nix_installation/index.html) in the docs.

### Conda
TBA

### Python-only Installation
You'll need to bring your own compiled tools, but otherwise, simply install OpenLane as follows:

```sh
python3 -m pip install --upgrade openlane
```

## Usage
In the root folder of the repository with the `venv` activated, you may invoke:

```sh
python3 -m openlane --pdk-root <path/to/pdk> </path/to/config.json>
```

To start with, you can try:

```sh
python3 -m openlane --pdk-root $HOME/.volare ./designs/spm/config.json
```
