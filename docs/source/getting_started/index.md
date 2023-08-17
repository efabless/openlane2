# Getting Started

OpenLane 2 offers two primary methods of installation: using **Nix** and using
**Docker**.

Nix installations offer:
* Filesystem integration: No need to worry about which folders are being mounted
* Smaller deltas: if one tool is updated, you do not need to re-download everything

Docker installations offer:
* Sandboxing: A completely different environment for using OpenLane
* Familiarity: Users of previous versions of OpenLane will already have Docker installed

Because of the advantages afforded by Nix, we recommend trying to install using
Nix first, and if it doesn't work, installing Docker.

```{toctree}
:glob:
:maxdepth: 2
   
nix_installation/index
docker_installation/index
quickstart
updating
```

## Wait, what if I don't want to use either of these?

Also an option! You will need to build and install the tools on your own,
however. A non-exhaustive list is:

* [Python 3.8 or higher](https://www.python.org/)
* [Yosys](https://yosyshq.net/)
* [OpenROAD](https://github.com/The-OpenROAD-Project/OpenROAD)
* [KLayout](https://klayout.de)
* [Magic](http://opencircuitdesign.com/magic/)
* [Netgen](http://opencircuitdesign.com/netgen/)

However, as the versions will likely not match those packaged with OpenLane,
some incompatibilities may arise, and we will not be able to support them.