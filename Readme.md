> OpenLane 2.0.0 is in beta. APIs have mostly stabilized, but some oddities are still to be expected. Proceed with caution.
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
    <a href="https://colab.research.google.com/github/efabless/openlane2/blob/main/notebook.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open in Colab"></a>
    <a href="https://openlane2.readthedocs.io/"><img src="https://readthedocs.org/projects/openlane2/badge/?version=latest" alt="Documentation Build Status Badge"/></a>
    <a href="https://invite.skywater.tools"><img src="https://img.shields.io/badge/Community-Open%20Source%20Silicon%20Slack-ff69b4?logo=slack" alt="Invite to the Open Source Silicon Slack"/></a>
</p>

OpenLane is a RTL to GDSII infrastructure library based on several components including OpenROAD, Yosys, Magic, Netgen, CVC, KLayout and a number of custom scripts for design exploration and optimization. A reference flow performs all ASIC implementation steps from RTL all the way down to GDSII.

You can find the documentation [here](https://openlane2.readthedocs.io/en/latest/getting_started/) to get started. You can discuss OpenLane 2 in the [#openlane-2](https://open-source-silicon.slack.com/archives/C05M85Q5GCF) channel of the [Efabless Open Source Silicon Slack](https://invite.skywater.tools).

```python
from openlane.flows import Flow

Classic = Flow.factory.get("Classic")

flow = Classic(
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

## Try it out
You can try OpenLane right in your browser, free-of-charge, using Google Colaboratory
by following [**this link**](https://colab.research.google.com/github/efabless/openlane2/blob/main/notebook.ipynb).

## Installation
You'll need the following:
* Python **3.8** or higher with PIP, Venv and Tkinter

### Nix (Recommended)
Works for macOS and Linux (x86-64 and aarch64). Recommended, as it is more integrated with your filesystem and overall has less upload and download deltas.

See [Nix-based installation](https://openlane2.readthedocs.io/en/latest/getting_started/nix_installation/index.html) in the docs for more info.

### Docker
Works for Windows, macOS and Linux (x86-64 and aarch64).

See [Docker-based installation](https://openlane2.readthedocs.io/en/latest/getting_started/docker_installation/index.html) in the docs for more info.

Do note you'll need to add `--dockerized` right after `openlane` in most CLI invocations.

### Python-only Installation (Advanced)
You'll need to bring your own compiled utilities, but otherwise, simply install OpenLane as follows:

```sh
python3 -m pip install --upgrade openlane
```

## Usage
In the root folder of the repository, you may invoke:

```sh
python3 -m openlane --pdk-root <path/to/pdk> </path/to/config.json>
```

To start with, you can try:

```sh
python3 -m openlane --pdk-root $HOME/.volare ./designs/spm/config.json
```

## Publication
If you use OpenLane in your research, please cite the following paper.

* M. Shalan and T. Edwards, “Building OpenLANE: A 130nm OpenROAD-based Tapeout-Proven Flow: Invited Paper,” *2020 IEEE/ACM International Conference On Computer Aided Design (ICCAD)*, San Diego, CA, USA, 2020, pp. 1-6. [Paper](https://ieeexplore.ieee.org/document/9256623)

```bibtex
@INPROCEEDINGS{9256623,
  author={Shalan, Mohamed and Edwards, Tim},
  booktitle={2020 IEEE/ACM International Conference On Computer Aided Design (ICCAD)}, 
  title={Building OpenLANE: A 130nm OpenROAD-based Tapeout- Proven Flow : Invited Paper}, 
  year={2020},
  volume={},
  number={},
  pages={1-6},
  doi={}}
```

## License
[The Apache License, version 2.0](https://www.apache.org/licenses/LICENSE-2.0.txt).

Docker images distributed by Efabless Corporation under the same license.

Binaries bundled with OpenLane either via Cachix or Docker are distributed by
Efabless Corporation and may fall under stricter open source licenses.
