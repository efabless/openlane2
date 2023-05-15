# Introduction
OpenLane 2 is a total rewrite of OpenLane in Python. The goal is to
create a more modular infrastructure with which more than one flow can be
implemented, but also have the flow be composed reusable blocks that can also be
utilized in other flows, and also enable the creation of robust complex flows
for more involved chip designs such as Caravel.

Where as OpenLane 1 was **monolithic**, i.e. one flow that (mostly) had to be run
in its entirety, OpenLane 2 is completely **modular**, with multiple flows composed of
execution units called **steps**. Each step roughly corresponds to one action
taken by an EDA tool.

## Do all my designs work?
Yes*! OpenLane 2 supports about 99% of the config files from OpenLane 1,
whether they're written in JSON or Tcl, although Tcl is finicky at this point and we recommend rewriting them in JSON.

\* Interactive scripts written in Tcl, however, are not supported in OpenLane 2-
we've replaced them with Python-based flows, which are much better: you can
check out how to write one [here](../writing_custom_flows.md).

## Is the installation process different?
A bit. There is no longer a need to clone the OpenLane repository for instance:
instead of `make openlane`, `make pdk` and `make mount`, you can simply just:

1. Install Docker.
2. Install Python with PIP.
3. Run `python3 -m pip install openlane`.

For more detailed instructions, see the full setup instructions [here](../../getting_started/docker_installation/index.md).

Then you can just invoke OpenLane as such:

```sh
python3 -m openlane --dockerized <arguments>
```

OpenLane will automatically pull the corresponding Docker image and the
PDK version it requires.

```{warning}
`--dockerized` will make your home folder, your PDK root and your current working directory available to the OpenLane Docker container.

If you need any other directories mounted, you can pass them in the following manner: `--docker-mount <dir1> [--docker-mount <dir2> [--docker-mount <dir3>]]`.
```

## Is the CLI usage the same?
No- there are some elements that are different:

* The design is no longer a flag, it's an argument, i.e., you do not need a `-design` or `--design` before the design configuration file.
* The design argument must be a fully-qualified path to the configuration file, not a folder, and it will not automatically look inside the `designs` folder of OpenLane.
* Options are now parsed GNU-style, i.e., long flags begin with `--` and short flags begin with `-`.

Here are some examples from OpenLane 1 and how you'd replace them in 2:

| OpenLane 1 | OpenLane 2+ |
| - | - |
| `flow.tcl -design spm -tag my_run` | `python3 -m openlane ./designs/spm/config.json --tag my_run`
| `flow.tcl -design xtea -verbose 2` | `python3 -m openlane ./designs/xtea/config.tcl --log-level VERBOSE` |
| `flow.tcl -design spm -last_run -from floorplan` | `python3 -m openlane ./designs/spm/config.json --from openroad.floorplan --last-run` (case-insensitive, [step names here](../../reference/flow_config_vars.md#classic)) |

## What else is different?
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

## I'm having trouble migrating a configuration file.
Some variables are particularly annoying to deal with: See [migrating variables](./variables.md) for more info.

If you can't find the variable causing your problems, feel free to just create
an issue [on GitHub](https://github.com/efabless/openlane2/issues/new) and
we'll get back to you as soon as we can.