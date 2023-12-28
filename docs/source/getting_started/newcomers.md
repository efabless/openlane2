# Newcomers

## What is OpenLane?

```{note}
Already know? Click [Here](#installation)
```

TODO: INSERT DIAGRAM HERE

OpenLane is a powerful and versatile infrastructure library that enables the
construction of digital ASIC implementation flows based on open-source and
commercial EDA tools. It includes a reference flow (Classic) that is built
entirely using open-source EDA tools, and it allows designers to abstract the
underlying tools and configure their behavior with a single configuration file.
OpenLane also supports the ability to freely extend or modify the flow using
Python scripts and utilities.

Here are some of the key benefits of using OpenLane:

- Flexibility and extensibility: OpenLane is designed to be flexible and
  extensible, allowing designers to customize the flow to meet their specific
  needs. This can be done by writing Python scripts and utilities, or by
  modifying the existing configuration file.

- Open source: OpenLane is an open-source project, which means that it is freely
  available to use and modify. This makes it a good choice for designers who are
  looking for a cost-effective and transparent solution.

- Community support: OpenLane capitalizes on OpenLane’s existing community of
  users and contributors. This means that there is a wealth of resources
  available to help designers get started and troubleshoot any problems they
  encounter.

```{note}
[Click here](https://developers.google.com/silicon/guides/digital-inverter-openlane)
to try out OpenLane using Google Colab directly in your browser.
You do not even need to install anything on your machine!
```

TODO INSERT SCREENSHOT COLLAB

## Installation

1. Follow instructions [here](https://app.cachix.org/cache/openlane) to install
   Nix and setup cachix.

2. Open up a terminal and clone OpenLane:

   ```bash
   git clone https://github.com/efabless/openlane2/ ~/openlane2
   ```

3. Run smoke test to install everything needed by OpenLane (packages from Nix
   and the PDK)
   ```bash
   nix-shell ~/openlane2/shell.nix --pure --run "openlane --smoke-test"
   ```

```{note}
This downloads about 20000 GB. It might take sometime depending on your connectivity.
Also, make sure to have enough storage.
```

That's it. Everything is setup. Now, let's try OpenLane.

## Running OpenLane

We are going to copy and run following example `spm` design:

:::{dropdown} spm.v

```{literalinclude} ../../../openlane/examples/spm/src/spm.v
:language: verilog
:lines: 14-
```

:::

Designs in OpenLane have configuration files. A configuration files contains
`Variables`. With them you control the OpenLane flow and set your design's
source files. For example, this is configuration file of `spm` design:

:::{dropdown} config.json

```{literalinclude} ../../../openlane/examples/spm/config.json
:language: json
```

:::

You can do that by running the following commands in the terminal:

```bash
mkdir ~/my_designs
cd ~/my_designs/
nix-shell ~/openlane2/shell.nix --pure --run "openlane --run-example spm"
```

That's it. Let's take a look at the results.

### Results

To open the final GDSII layout run this command:

```console
[nix-shell:~/openlane2]$ nix-shell ~/openlane/shell.nix --pure --run "openlane --last-run --flow openinklayout ./spm/config.json"
```

You should be able to see the following:

```{image} ./spm-gds.png
:align: center
```

If you wish to use OpenROAD GUI use the following:

```bash
nix-shell ~/openlane/shell.nix --pure --run "openlane --last-run --flow openinopenroad ./spm/config.json"
```

A new **run folder** (named something like `runs/RUN_2023-12-27_16-59-15`)
should have been created.

The run directory structure looks like this:

```
RUN_2023-12-27_16-59-15
├── 01-verilator-lint
├── 02-checker-linttimingconstructs
├── 03-checker-linterrors
├── 04-yosys-jsonheader
├── 05-yosys-synthesis
├── 06-checker-yosysunmappedcells
├── 07-checker-yosyssynthchecks
├── 08-openroad-checksdcfiles
├── 09-openroad-staprepnr
├── 10-openroad-floorplan
├── 11-odb-setpowerconnections
├── 12-odb-manualmacroplacement
├── 13-openroad-cutrows
├── 14-openroad-tapendcapinsertion
├── 15-openroad-globalplacementskipio
⋮
├── final
├── tmp
├── error.log
├── info.log
├── resolved.json
└── warning.log
```

This runs a `Flow` composed of a sequence of `Step`(s). Each `Step` creates a
directory.

For example, the `OpenROAD.TapEndCapInsertion` `Step` creates the following
directory: `14-openroad-tapendcapinsertion`

Additionally, you can view the layout at each `Step`:

```bash
nix-shell ~/openlane/shell.nix --pure --run "openlane --last-run --flow openinklayout ~/my_designs/spm/config.json --with-initial-state ~/my_designs/spm/runs/RUN_2023-12-27_16-59-15/14-openroad-tapendcapinsertion/state_out.json"
```
