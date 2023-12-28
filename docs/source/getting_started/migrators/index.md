!register migration_comparison

# Migrating from OpenLane 1

OpenLane 2 is a complete re-imagining of OpenLane not just as a simple, somewhat
customizable flow, but rather as an infrastructure that can support innumerable
flows.

## Why migrate?

At a minimum, the default flow for OpenLane 2, named `Classic`, is essentially a
more robust re-implementation of the OpenLane 1 flow that is still entirely
backwards compatible, with some conveniences:

* Full configuration validation: if you have a typo, it will be caught, and if
  you accidentally provide a string to a number, it will be caught.
* More graceful failures: if the design fails mid-flow, because of a more strict
  separation of concerns, you still have access to metrics and reports from all
  previous steps.
  * In OpenLane 1, they are all extracted at the end.
* The ability to use command-line flow control options such as `--from`, `--to`,
  `--skip` and `--only`, with the ability to resume from a snapshot of your
  design at a certain part of the flow, without worrying about surprises related
  to state variables missing.

Additionally, if you're a more savvy user, a *whole new world* of possibilities
await with OpenLane 2. Built around "flows" composed of "steps," OpenLane 2 can
implement hardware flows for ASIC implementation by relying on basic Python
object-oriented programming principles, and this naturally allows you to:

* Write your own step, in Python. For example, create a custom placement step
  for your design using OpenROAD Tcl or Python scripts, or even completely
  custom code.
* Write complex flows with decision-making capabilities, including the ability
  to repeat some steps or even try multiple strategies simultaneously and
  proceed with the best result.
  * You can even do this in a Python Notebook!
* Access a standardized and more formal form of design metrics based on
  https://github.com/ieee-ceda-datc/datc-rdf-Metrics4ML.

For example, using a custom OpenLane 2-based flow, the team over at
[TinyTapeout](https://tinytapeout.com) were able to integrate dozens of tiny
designs together into a complex chip; leveraging custom flows and custom steps
to tape-out a complex chip for ChipIgnite.

## Do all my designs work?

Yes*! OpenLane 2 supports about 99% of the config files from OpenLane 1,
whether they're written in JSON or Tcl, although Tcl is finicky at this point
and we recommend rewriting them in JSON.

\* Interactive scripts written in Tcl, however, are not supported in OpenLane 2-
we've replaced them with Python-based flows, which are much better: you can
check out how to write one [here](../writing_custom_flows.md).

## Installation

Like OpenLane 1, installations of OpenLane 2 include all underlying utilities
for the default flow, including but not limited to; Yosys, OpenROAD, Magic, and
KLayout.

OpenLane 2 uses a deterministic and reproducible environment builder called
[Nix](https://nixos.org) to both build its underlying utilities and distribute
them.

While using a Dockerized environment is still supported yields a number of
advantages and is overall recommended.

### Nix-based Installation (Recommended)

The Nix method involves installing the Nix build utility/package management
software and cloning the OpenLane repository.

You can install Nix and set up the OpenLane binary cache by following the
instructions at [Cachix](https://openlane.cachix.org).

For more detailed instructions, see
[Nix installation](./nix_installation/index.md).

Afterwards, you can run an example as follows:

```{include} ../common/nix_installation/_running_example.md
```

### Docker-based Installation

Docker is still supported if you have it installed from OpenLane 1, although the
Docker image is built with a Nix environment instead of CentOS. The way it is
invoked is also much simpler, with the Python script handling mounts and calling
the image for you, as you can see below:

```!migration_comparison
git clone https://github.com/The-OpenROAD-Project/OpenLane
make pdk
make mount 
./flow.tcl -design spm
---
pip3 install --upgrade openlane
openlane --dockerized --run-example spm
---
This allows you to start the OpenLane environment from anywhere, without having
to rely on a Makefile.
```

```{warning}
`--dockerized` will make your home folder, your PDK root and your current
working directory available to the OpenLane Docker container.

If you need any other directories mounted, you can pass them in the following
manner: `--docker-mount <dir1> [--docker-mount <dir2> [--docker-mount <dir3>]]`.
```

## Command-line Interface

The command line interface for OpenLane 2 is more streamlined, and entirely
handled by the OpenLane 2 Python module instead of relying on Makefiles.

```!migration_comparison ### PDK Installation
make pdk
---
---
OpenLane 2 will automatically download and install the default PDK(s) version
using Volare.
```

```!migration_comparison ### Installation Smoke-Testing
make test
---
openlane [--dockerized] --smoke-test 
---
Being built into the command-line interface of OpenLane makes it runnable from
anywhere.
```

```!migration_comparison ### Running an example design
./flow.tcl -design spm
---
openlane --run-example spm
---
The example designs are now copied to the current working directory before being
run, instead of relying on a global "OpenLane installation" directory.
```

```!migration_comparison ### Running your own design
./flow.tcl ~/my_designs/picorv32
---
openlane --run-example spm
---
We've done away with providing the design folder and automatically trying to
detect which configuration file should be run, instead opting to use the
configuration file automatically.
```

## Output Folder Structure

We've taken the liberty of vastly improving the run folders while we're at it:
instead of a haphazardly strewn set of meta-step folders, each step now has its
own folder. Here's an example for the default flow:

By inspecting a step's folder, you'll find its outputs, including design views,
logs and reports.

```
.
├── 01-yosys-synthesis
├── 02-checker-yosysunmappedcells
├── 03-misc-loadbasesdc
├── 04-openroad-netliststa
├── 05-openroad-floorplan
├── 08-openroad-tapendcapinsertion
├── 09-openroad-ioplacement
├── 11-openroad-generatepdn
├── 12-openroad-globalplacement
├── 13-odb-diodesonports
├── 15-openroad-repairdesign
├── 16-openroad-detailedplacement
├── 17-openroad-cts
├── 18-openroad-resizertimingpostcts
├── 19-openroad-globalrouting
├── 20-openroad-resizertimingpostgrt
├── 21-openroad-detailedrouting
├── 22-checker-trdrc
├── 23-odb-reportwirelength
├── 25-openroad-fillinsertion
├── 26-openroad-rcx
├── 27-openroad-parasiticssta
├── 28-openroad-irdropreport
├── 29-magic-streamout
├── 30-klayout-streamout
├── 31-klayout-xor
├── 32-magic-drc
├── 33-checker-magicdrc
├── 34-magic-spiceextraction
├── 35-checker-illegaloverlap
├── 36-netgen-lvs
└── 37-checker-lvs
```
