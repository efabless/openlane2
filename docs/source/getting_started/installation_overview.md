# Installation Overview

OpenLane 2 offers two primary methods of installation: using **Nix** and using
**Docker**.

## Nix (Recommended)

Because of the advantages afforded by Nix, we recommend trying to install using
Nix first. Follow the installation guide here:
{ref}`nix-based-installation`

## Docker (Alternative)

Docker containers offer:

* Support for Windows, Mac and Linux on both `x86-64` and `aarch64`
* **Sandboxing:** A completely different environment for using OpenLane
* **Familiarity:** Users of previous versions of OpenLane will already have
  Docker installed

If Nix doesn't work for you for whatever reason, you may want to try Docker.
Follow the installation guide here:
[Docker-based Installation](./common/docker_installation/index.md).

## Other Options

You may elect to somehow provide the tools yourself. Here is a non-exhaustive
list:

* [Python 3.8 or higher](https://www.python.org/)
* [Yosys](https://yosyshq.net/)
* [OpenROAD](https://github.com/The-OpenROAD-Project/OpenROAD)
* [KLayout](https://klayout.de)
* [Magic](http://opencircuitdesign.com/magic/)
* [Netgen](http://opencircuitdesign.com/netgen/)

However, as the versions will likely not match those packaged with OpenLane,
some incompatibilities may arise, and we will not be able to support them.
