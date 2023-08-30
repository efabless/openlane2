# Getting Started

OpenLane 2 offers two primary methods of installation: using **Nix** and using
**Docker**.

## Nix (Recommended)

Nix offers:

* Support for Mac, Linux, and the Windows Subsystem for Linux on x86-64
* **Filesystem integration:** No need to worry about which folders are being mounted
* **Smaller deltas:** if one tool is updated, you do not need to re-download everything
* **Dead-simple customization:** You can modify any tool versions and/or any
  OpenLane code and all you need to do is re-invoke `nix-shell`. Nix's smart
  cache-substitution feature will automatically figure out whether your build
  is cached or not, and if not, will automatically attempt to build any tools
  that have been changed.

Because of the advantages afforded by Nix, we recommend trying to install using
Nix first. Follow the installation guide here: [Nix-based Installation](./nix_installation/index.md).

```{note}
Nix build scripts are currently only available and supported for x86-64.
If you're on aarch64 (Apple Silicon or similar,) you may be able to use the
x86-64 version of Nix via emulators such as Qemu or Rosetta, but you would be
on your own, or you can try Docker below.
```

## Docker (Alternative)

Docker containers offer:

* Support for Windows, Mac and Linux on x86-64
    * Using Docker's **transparent emulation**, support for aarch64 with a
      minor (but noticeable) performance penalty
* **Sandboxing:** A completely different environment for using OpenLane
* **Familiarity:** Users of previous versions of OpenLane will already have Docker installed

If Nix doesn't work for you for whatever reason, you may want to try Docker.
Follow the installation guide here: [Docker-based Installation](./docker_installation/index.md).

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

```{toctree}
:glob:
:maxdepth: 2
   
nix_installation/index
docker_installation/index
quickstart
updating
```
