# Newcomers

## What is OpenLane?

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

```{seealso}
[Click here](https://developers.google.com/silicon/guides/digital-inverter-openlane)
to try out OpenLane using Google Colab directly in your browser.
You do not even need to install anything on your machine!
```

```{note}
This guide assumes that the reader has some basic knowledge of ASIC, Digital Design,
JSON and RTL
```

TODO INSERT SCREENSHOT COLLAB

---

## Installation

1. Follow instructions [here](https://app.cachix.org/cache/openlane) to install
   [Nix](#glossary) and setup [cachix](#glossary).

2. Open up a terminal and clone OpenLane:

   ```console
   $ git clone https://github.com/efabless/openlane2/ ~/openlane2
   ```

3. Enter `nix-shell` which is similar to a virtual environment. It allows all
   the packages bundled with OpenLane

   ```console
   $ nix-shell --pure
   ```

   Some packages will be downloaded (about 3GBs) and the terminal prompt should change
   to:

   ```console
   [nix-shell:~/openlane2]$
   ```

   :::{admonition} Important
   :class: tip

   From now on all the commands assume
   that you are inside `nix-shell`.
   :::

4. Run the smoke test to ensure everything is fine.
   This also downloads [sky130A](#glossary) [PDK](#glossary).

   ```console
   [nix-shell:~/openlane2]$ openlane --log-level ERROR --condesed --show-progress-bar --smoke-test
   ```

That's it. Everything is setup. Now, let's try OpenLane.

---

## Running the default flow

We are going to harden a macro. A macro by itself has no function. It needs to be
integerated with a chip in order to server its purpose.

### SPM example

Let's try the following example `spm` design:

#### RTL

This is the source [RTL](#glossary) of the design.

:::{dropdown} spm.v

```{literalinclude} ../../../../openlane/examples/spm/src/spm.v
:language: verilog
:lines: 14-
```

:::

---

#### Configuration

Designs in OpenLane have configuration files. A configuration file contains
[Variable](#glossary)(s). With them you control the OpenLane flow and set your
design's source files. For example, this is configuration file of `spm` design:

:::{dropdown} config.json

```{literalinclude} ../../../../openlane/examples/spm/config.json
:language: json
```

:::

```{seealso}
For a full list of available configuration variables [click here]()
```

Notice variable `RT_MAX_LAYER` is set to `met4` and `FP_PDN_MULTILAYER`
is set to `False` such that the maxium routing layer `met5` is available
for [PDN](#glossary) connectivity while integrating the macro inside the chip.

#### How to run ?

```console
[nix-shell:~/openlane2]$ mkdir ~/my_designs
[nix-shell:~/openlane2]$ cd ~/my_designs/
[nix-shell:~/openlane2]$ openlane --run-example spm
```

That's it. Let's take a look at the results.

---

### Results

#### Viewing the layout

To open the final [GDSII](#glossary) layout run this command:

```console
[nix-shell:~/openlane2]$ openlane --last-run --flow openinklayout ~/my_designs/spm/config.json
```

This opens [KLayout](#glossary) and you should be able to see the following:

```{image} ./spm-gds.png
:align: center
```

If you wish to use [OpenROAD](#glossary) GUI use the following:

```console
[nix-shell:~/openlane2]$ openlane --last-run --flow openinopenroad ~/my_designs/spm/config.json
```

---

#### Output directory

A new **run folder** (named something like `runs/RUN_2023-12-27_16-59-15`)
should have been created.

By default, OpenLane runs a [Flow](#glossary) composed of a sequence of [Step](#glossary)(s).
Each `Step` has its separate folder.

For example, the `OpenROAD.TapEndCapInsertion` `Step` creates the following
folder `14-openroad-tapendcapinsertion` which would be inside the run folder.

A `Step` folder has log files, report files, [metrics](#glossary)
and output artifacts created by the `Step`.
For example, these are the contents of `14-openroad-tapendcapinsertion`:

```text
14-openroad-tapendcapinsertion/
├── COMMANDS
├── config.json
├── openroad-tapendcapinsertion.log
├── openroad-tapendcapinsertion.process_stats.json
├── or_metrics_out.json
├── spm.def
├── spm.nl.v
├── spm.odb
├── spm.pnl.v
├── spm.sdc
├── state_in.json
└── state_out.json
```

Here is a small description of each file inside a `Step` directory.
:::{dropdown} An example of Step directory contents

- `COMMANDS`: the CLI command of the underlying tool used by a `Step`
- `config.json`: contains `Variables` used by the `Step`
- `*.log`: one or more log file of the `Step`
- `*.process_stats.json`: statistics about total elapsed time and resource consumption
- `state_in.json`: contains a dictionary of design artifacts (TODO:correct word?) (such as `DEF` file)
  and design `Metrics` available as inputs to a `Step` .
- `state_out.json`: An updated `state_in.json`. For example, If a step generates
  a new `DEF` file it would be updated otherwise, it is a copy of `state_in.json`.
- `or_metrics_out.json`: It contains new or updated `Metrics` generated by the
  step.
- `spm.nl.v`: A `Verilog` gate-level netlist generated by the step **without**
  power connections
- `spm.pnl.v`: A `Verilog` gate-level netlist generated by the step **with** power
  connections
- `spm.odb`: Design database format of `OpenROAD` generated by the step.
- `spm.def`: The design in `DEF` format generated by the step.
- `spm.sdc`: `SDC` stands for Synopsis Design Constraints. It describes timing
  constraints used during [STA](#sta)

:::

The run directory structure looks like this:

```text
RUN_2023-12-27_16-59-15
├── 01-verilator-lint/
├── 02-checker-linttimingconstructs/
├── 03-checker-linterrors/
├── 04-yosys-jsonheader/
├── 05-yosys-synthesis/
├── 06-checker-yosysunmappedcells/
├── 07-checker-yosyssynthchecks/
├── 08-openroad-checksdcfiles/
├── 09-openroad-staprepnr/
├── 10-openroad-floorplan/
├── 11-odb-setpowerconnections/
├── 12-odb-manualmacroplacement/
├── 13-openroad-cutrows/
├── 14-openroad-tapendcapinsertion/
├── 15-openroad-globalplacementskipio/
⋮
├── final/
├── tmp
├── error.log
├── info.log
├── resolved.json
└── warning.log
```

Additionally, you can view the layout at each `Step`:

```console
[nix-shell:~/openlane2]$ openlane --last-run --flow openinklayout ~/my_designs/spm/config.json --with-initial-state ~/my_designs/spm/runs/RUN_2023-12-27_16-59-15/14-openroad-tapendcapinsertion/state_out.json"
```

#### Final Results

Inside the run folder, there is a folder called `final`. This folder contains
other folders that contina all the different layout views produced by the flow
such as [DEF](#glossary), [LEF](#glossary), `GDSII` and others. It looks like
this:

```text
final
├── def/
├── gds/
├── json_h/
├── klayout_gds/
├── lef/
├── lib/
├── mag/
├── mag_gds/
├── nl/
├── odb/
├── pnl/
├── sdc/
├── sdf/
├── spef/
├── spice/
├── metrics.csv
└── metrics.json
```

Additionally, it contains `metrics.csv` and `metric.json` which represents the
final `metrics` in `JSON` and [CSV](#glossary) formats

---

### Important Steps

OpenLane runs a couple of `Step`(s) as checks attempting to verify the manufacturability
and functionality of the design:

1. [DRC](#glossary)
2. [LVS](#glossary)
3. [STA](#glossary)

#### DRC

`DRC` stands for Design Rule Checking which are set by the [foundary](#glossary)
,sometimes as guidlines, but mostly strict rules that the design has to satisfy
in order to be manufacturable. Such as, the spacing between two `met1` layers.

OpenLane runs two `DRC` steps using different layout tools: `Magic.DRC` and
`KLayout.DRC`. Inside each step folder you will a report file viewable using
KLayout called TODO:INSERT_FILE_NAME_HERE

In addition, if `DRC` errors are found OpenLane will generate an error reporting
the total count of violations found by each`Step`.

To view `DRC` errors. Open the layout, as mentioned [here](#viewing-the-layout)
Then in the menu bar select Tools -> Marker Browser. A new window should open.
Then select File -> import.

```{image} ./klayout-markerbrowser-menu.png
:align: center
```

#### LVS

`LVS` stands for Layout Versus Schematic. It compares the layout `GDSII` or
`DEF`/`LEF`, with the schematic which is usually in [Verliog](#glossary) ensuring
that connectivity in both views are matching. Sometimes, user configuration or
even the tools have errors and such check is important to catch them.

`Netgen.LVS` is the `Step` ran for `LVS` using a tool called [Netgen](#glossary).
It will generate multiple files which can be browsed in case of `LVS` errors.
As all `Step`(s), these will be inside the `Step`'s folder.

You would want to look at `netgen-lvs.log`. This has a summary of the results of
`LVS`. Ideally you would find the following at the end of this log file:

```text
Final result:
Circuits match uniquely.
```

In case of errors, there is also `lvs.rpt` which contains the detailed comparison
between the layout and the schematic. It contains table comparing nodes between them.
On the left is the layout (`GDS`) and the schematic (`Verilog`) is on the other side.
Here is a sample of these tables.

```text
Subcircuit summary:
Circuit 1: spm                             |Circuit 2: spm
-------------------------------------------|-------------------------------------------
sky130_fd_sc_hd__tapvpwrvgnd_1 (102->1)    |sky130_fd_sc_hd__tapvpwrvgnd_1 (102->1)
sky130_fd_sc_hd__decap_3 (144->1)          |sky130_fd_sc_hd__decap_3 (144->1)
sky130_fd_sc_hd__inv_2 (64)                |sky130_fd_sc_hd__inv_2 (64)
sky130_fd_sc_hd__nand2_1 (31)              |sky130_fd_sc_hd__nand2_1 (31)
sky130_fd_sc_hd__dfrtp_1 (64)              |sky130_fd_sc_hd__dfrtp_1 (64)
sky130_ef_sc_hd__decap_12 (132->1)         |sky130_ef_sc_hd__decap_12 (132->1)
```

```{seealso}
TODO Checkout our guide of common LVS errors.
```

#### STA

`STA` stands for Static Timing Analysis. TODO: Insert description here

The default flow runs multiple `STA` `Step`(s) `OpenROAD.STAPostPNR` is the
final `STA` `Step` and the most important one to check.

Inside its run folder there is a file called `summary.rpt` which summarizes
important metrics for each <TODO: Check TIMNING?> [corner](#glossary):

```text
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃             ┃ Hold Worst  ┃ Hold        ┃ of which    ┃ Setup Worst ┃ Setup       ┃ of which    ┃ Max Cap     ┃ Max Slew   ┃
┃ Corner/Gro… ┃ Slack       ┃ Violations  ┃ reg-to-reg  ┃ Slack       ┃ Violations  ┃ reg-to-reg  ┃ Violations  ┃ Violations ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Overall     │ 0.1115      │ 0           │ 0           │ 5.9742      │ 0           │ 0           │ 0           │ 0          │
│ nom_tt_025… │ 0.3308      │ 0           │ 0           │ 6.8067      │ 0           │ 0           │ 0           │ 0          │
│ nom_ss_100… │ 0.9046      │ 0           │ 0           │ 5.9894      │ 0           │ 0           │ 0           │ 0          │
│ nom_ff_n40… │ 0.1127      │ 0           │ 0           │ 7.1209      │ 0           │ 0           │ 0           │ 0          │
│ min_tt_025… │ 0.3293      │ 0           │ 0           │ 6.8173      │ 0           │ 0           │ 0           │ 0          │
│ min_ss_100… │ 0.9046      │ 0           │ 0           │ 6.0068      │ 0           │ 0           │ 0           │ 0          │
│ min_ff_n40… │ 0.1115      │ 0           │ 0           │ 7.1289      │ 0           │ 0           │ 0           │ 0          │
│ max_tt_025… │ 0.3324      │ 0           │ 0           │ 6.7966      │ 0           │ 0           │ 0           │ 0          │
│ max_ss_100… │ 0.9072      │ 0           │ 0           │ 5.9742      │ 0           │ 0           │ 0           │ 0          │
│ max_ff_n40… │ 0.1138      │ 0           │ 0           │ 7.1133      │ 0           │ 0           │ 0           │ 0          │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┴─────────────┴─────────────┴─────────────┴────────────┘
```

There is also a folder per corner inside the `Step` directory which contains all
the log files and reports generated for each `corner`.

```text
nom_tt_025C_1v80/
├── checks.rpt
├── filter_unannotated.log
├── filter_unannotated.process_stats.json
├── filter_unannotated_metrics.json
├── max.rpt
├── min.rpt
├── power.rpt
├── skew.max.rpt
├── skew.min.rpt
├── spm__nom_tt_025C_1v80.lib
├── spm__nom_tt_025C_1v80.sdf
├── sta.log
├── sta.process_stats.json
├── tns.max.rpt
├── tns.min.rpt
├── violator_list.rpt
├── wns.max.rpt
├── wns.min.rpt
├── ws.max.rpt
└── ws.min.rpt
```

Here is a small description of each file:

- `sta.log`: Full log file generated by `STA` which is divided to the following
  report files
- `min.rpt`: Constrained paths for hold checks.
- `max.rpt`: Constrained paths for setup checks.
- `skew.min.rpt`: Maximum clock skew for hold checks.
- `skew.max.rpt`: Maximum clock skew for setup checks.
- `tns.min.rpt`: Total negative hold slack.
- `tns.max.rpt`: Total negative setup slack.
- `wns.min.rpt`: Worst negative hold slack.
- `wns.max.rpt`: Worst negative setup slack.
- `ws.min.rpt`: Worst hold slack.
- `ws.max.rpt`: Worst setup slack.
- `violator_list.rpt` Setup and hold violator endpoints.
- `checks.rpt`: It contains a summary of the following checks:

  1. Max capacitance violations
  2. Max slew violations
  3. Max fanout violations
  4. Unconstrained paths
  5. Unannotated and partially annotated nets
  6. Checks the `SDC` for comobinationals loops, register/latch with multiple clocks
     or no clocks, ports missing input delay and generated clocks
  7. Worst setup or hold violating path

Should check out our [STA guide](#doc-shalaan-docu) for more in depth details.

---

## Glossary
