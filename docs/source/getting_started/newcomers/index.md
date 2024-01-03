# Newcomers

## What is OpenLane ?

```{figure} ./flow.png
:scale: 30 %
:align: right

OpenLane Flow
```

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
Checkout [OpenLane using Google Colab directly in your browser](https://developers.google.com/silicon/guides/digital-inverter-openlane)
You do not even need to install anything on your machine!
```

```{note}
This guide assumes that the reader has some basic knowledge of ASIC, Digital Design,
JSON and RTL
```

---

## Installation

1. Follow instructions [here](https://app.cachix.org/cache/openlane) to install
   [Nix](../../glossary.md#term-Nix) and setup [cachix](../../glossary.md#term-cachix).

2. Open up a terminal and clone OpenLane:

   ```console
   $ git clone https://github.com/efabless/openlane2/ ~/openlane2
   ```

3. Enter `nix-shell` which is similar to a virtual environment. It allows all
   the packages bundled with OpenLane

   ```console
   $ nix-shell --pure ~/openlane2/shell.nix
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
   This also downloads [sky130](../../glossary.md#term-sky130) [PDK](../../glossary.md#term-PDK).

   ```console
   [nix-shell:~/openlane2]$ openlane --log-level ERROR --condesed --show-progress-bar --smoke-test
   ```

That's it. Everything is setup. Now, let's try OpenLane.

---

## Running the default flow

### SPM example

We are going to use a simple design: a serial-by-parallel signed
32-bit multiplier `SPM`. This multiplier performs the familiar shift-add algorithm.
The parallel input `a` is multiplied by each bit of the serial input `x` as it is
shifted in. The output is generated serially on `y`. Typically, SPM is interfaced
with 3 registers. One parallel register to provide the multiplier. Two shift
registers to provide the multiplicand and to get the serial product (64-bit).

```{figure} ./spm-block-diagram.png
:scale: 60 %
:align: center

SPM (Serial-by-Parallel Multiplier)
```

#### RTL

This is the source [RTL](../../glossary.md#term-RTL) of the design.

:::{dropdown} spm.v

```{literalinclude} ../../../../openlane/examples/spm/src/spm.v
:language: verilog
```

:::

#### Configuration

Designs in OpenLane have configuration files. A configuration file contains
[Variable](../../glossary.md#term-Variable)(s). With them you control the OpenLane flow
and set your design's source files. This is configuration file for `spm` design:

:::{dropdown} config.json

```json
{
  "DESIGN_NAME": "spm",
  "VERILOG_FILES": "dir::spm.v",
  "CLOCK_PERIOD": 10,
  "CLOCK_PORT": "clk"
}
```

:::

(required-variables)=

:::{warning}
You need to at least specify `DESIGN_NAME`, `VERILOG_FILES`, `CLOCK_PERIOD`
and `CLOCK_PORT` for any design.
:::

:::

```{seealso}
The [full list INSERT REFERENE HERE](#glossary) of available configuration variables.
```

#### How to run?

1. Let's create a folder to add our source files to:

   ```console
   [nix-shell:~/openlane2]$ mkdir -p ~/my_designs/spm
   ```

2. Create the file `~/my_designs/spm/config.json` and add [configuration](#configuration)
   content to it.

3. Create the file `~/my_designs/spm/spm.v` and add [RTL](#rtl) content to it.

4. Run the following command:

   ```console
   [nix-shell:~/openlane2]$ openlane ~/my_designs/spm/config.json
   ```

:::{tip}
Are you inside a `nix-shell` ? Your terminal prompt should look like this:

```console
[nix-shell:~/openlane2]$
```

If not, enter the following command in your terminal

```console
$ nix-shell --pure ~/openlane2/shell.nix
```

:::

---

#### SPM as a macro for [Caravel User Project](#https://caravel-user-project.readthedocs.io/en/latest/)

Usually a design is integerated as a macro inside a chip and by itslef it surves
no purpose. We are going to harden `spm` as a macro inside to be integrated inside
[Caravel User Project Wrapper](#https://caravel-user-project.readthedocs.io/en/latest/)

##### New RTL

Create a new folder `~/my_designs/spm-user_project_example/` and
add the following new `RTL` to `~/my_designs/spm-user_project_example/SPM_example.v`:

:::{dropdown} SPM_example.v

```{literalinclude} ../../../../openlane/examples/spm-user_project_example/SPM_example.v

```

:::

We need an additional file `~/my_designs/spm-user_project_example/defines.v` required
by `Caravel User Project`.

:::{dropdown} defines.v

```{literalinclude} ../../../../openlane/examples/spm-user_project_example/defines.v

```

:::

:::{seealso}
Checkout [Caravel User Project#Verilog Integration](https://caravel-user-project.readthedocs.io/en/latest/#verilog-integration)
for information about the `RTL` changes.
:::

##### New Configuration

We also need to update the configuration as follows.

:::{dropdown} config.json

```json
{
  "DESIGN_NAME": "SPM_example",
  "VERILOG_FILES": ["dir::./defines.v", "dir::./SPM_example.v"],
  "CLOCK_PERIOD": 25,
  "CLOCK_PORT": "wb_clk_i",
  "CLOCK_NET": "SPM.clk",
  "RT_MAX_LAYER": "met4",
  "FP_SIZING": "absolute",
  "VDD_NETS": ["vccd1"],
  "GND_NETS": ["vssd1"],
  "FP_PDN_MULTILAYER": false,
  "DIE_AREA": [0, 0, 600, 600]
}
```

:::

Aside from the [required variables](#required-variables), we also change the following:

- `RT_MAX_LAYER` and `FP_PDN_MULTILAYER`: `sky130A` maximum routing layer is `met5`.
  We are going to integerate to integrate it as macro inside another design.
  The outer design's `PDN` is going to connect to our macro via `met5`. Hence
  we make that layer completely available by limiting maximum routing layer to
  `met4` and disabling `FP_PDN_MULTILAYER` which disable `met5` `PDN` pins in our
  macro.
- `FP_SIZING` and `DIE_AREA`: Due to requirements set by `Caravel User Project`,
  we need a fixed area for our macro. We do that by setting `FP_SIZING` to `absolute`
  and setting `DIE_AREA` to our required area.
- `VDD_NETS` and `GND_NETS`: Also due to requirements set by `Caravel User Project`,
  we set power and ground nets to `vccd1` and `vssd1`.

---

### Results of SPM as core ?

#### Viewing the Layout

To open the final [GDSII](../../glossary.md#term-GDSII) layout run this command:

```console
[nix-shell:~/openlane2]$ openlane --last-run --flow openinklayout ~/my_designs/spm/config.json
```

This opens [KLayout](../../glossary.md#term-KLayout) and you should be able to see the following:

```{figure} ./spm-gds.png
:align: center

Final GDSII view of SPM #TODO CROP
```

If you wish to use [OpenROAD](../../glossary.md#term-OpenROAD) GUI use the following:

```console
[nix-shell:~/openlane2]$ openlane --last-run --flow openinopenroad ~/my_designs/spm/config.json
```

---

#### Run folder

A new **run folder** (named something like `runs/RUN_2023-12-27_16-59-15`)
should have been created.

By default, OpenLane runs a [Flow](../../glossary.md#term-Flow) composed of a
sequence of [Step](../../glossary.md#term-Step)(s).
Each `Step` has its separate folder.

For example, the `OpenROAD.TapEndCapInsertion` `Step` creates the following
folder `14-openroad-tapendcapinsertion` which would be inside the run folder.

A `Step` folder has log files, report files, [Metrics](../../glossary.md#term-Metrics)
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
:::{dropdown} OpenROAD.TapEndCapInsertion Step directory contents

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

##### Viewing Intermediate Layout

Additionally, you can view the intermediate layout at each `Step`:

```console
[nix-shell:~/openlane2]$ openlane --last-run --flow openinklayout ~/my_designs/spm/config.json --with-initial-state ~/my_designs/spm/runs/RUN_2023-12-27_16-59-15/14-openroad-tapendcapinsertion/state_out.json"
```

#### Final Results

Inside the run folder, there is a folder called `final`. This folder contains
other folders that contains all the different layout views produced by the flow
such as [DEF](../../glossary.md#term-DEF), [LEF](../../glossary.md#term-LEF),
`GDSII` and others. It looks like this:

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

Moreover, it contains `metrics.csv` and `metric.json` which represents the
final `metrics` in `JSON` and [CSV](../../glossary.md#term-CSV) formats

---

### Signoff Steps

An ASIC design’s signoff is the last phase of implementation. It requires physical
and timing verifications before committing to the silicon manufacturing process,
which is commonly known as design tape-out.

OpenLane runs a couple of `Step`(s) for the final signoff.

1. [DRC](#drc)
2. [LVS](#lvs)
3. [STA](#sta)

#### DRC

`DRC` stands for Design Rule Checking which are set by the FOUNDRY/Chip Manfucturer?
rules that the layout has to satisfy in order to be manufacturable.
Such as, checking for minimum allowed spacing between two `met1` shapes.

OpenLane runs two `DRC` steps using `Magic` and `KLayout`: `Magic.DRC` and
`KLayout.DRC`. The Layout and `PDK` [DRC deck] are inputed to the tools running
DRC, as shown in the diagram bellow:

```{figure} ./OL-DRC.png
:align: center
:scale: 50 %

DRC (Design Rule Checking) Flow
```

If `DRC` errors are found OpenLane will generate an error reporting
the total count of violations found by each `Step`.

To view `DRC` errors graphically. Open the layout, as mentioned in [Viewing the Layout](#viewing-the-layout).
Then in the menu bar select Tools -> Marker Browser. A new window should open.
Then select File -> import and then select the report file you would like to open.
Report files will be found under `52-magic-drc/reports/drc.klayout.xml` and
`53-klayout-drc/report/drc.klayout.xml`

:::{tip}
The intial number in `53-klayout-drc` (`53`) may vary according to a design configuration.
:::

```{image} ./klayout-markerbrowser-menu.png
:align: center
```

TODO: MORE SCREENSHOTS AND HIGHLIGHT BOXES

#### LVS

`LVS` stands for Layout Versus Schematic. It compares the layout `GDSII` or
`DEF`/`LEF`, with the schematic which is usually in
[Verilog](../../glossary.md#term-Verilog) ensuring that connectivity in both
views are matching. Sometimes, user configuration or even the tools have errors
and such check is important to catch them.

Common `LVS` errors include but are not limited to:

- Shorts: Two or more wires that should not be connected have been and must be
  separated. The most problematic is power and ground shorts.
- Opens: Wires or components that should be connected are left dangling or only
  partially connected. These must be connected properly.
- Missing Components: An expected component has been left out of the layout.

`Netgen.LVS` is the `Step` ran for `LVS` using a tool called
[Netgen](../../glossary.md#term-Netgen). First, the layout is converted to
[SPICE](../../glossary.md#term-SPICE). Next
the layout and the schematic are inputed to Netgen, as shown in the digram
bellow.

```{figure} ./OL-LVS.png
:scale: 50 %
:align: center

LVS (Layout-versus-Schematic) Flow
```

`Netgen` will generate multiple files which can be browsed in case of `LVS` errors.
As all `Step`(s), these will be inside the `Step`'s folder.

You would want to look at `netgen-lvs.log`. This has a summary of the results of
`LVS`. Ideally you would find the following at the end of this log file:

```text
Final result:
Circuits match uniquely.
```

In case of errors, there is also `lvs.rpt` which more detailed. Inside it you will
find tables comparing nodes between the layout and the schematic.
On the left is the layout (`GDS`) and the schematic (`Verilog`) is on the other side.
Here is a sample of these tables:

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

#### STA

`STA` stands for Static Timing Analysis. The STA tool identifies the design timing
paths and then calculates the data earliest and latest actual and required arrival
times at every timing path endpoint. If the data arrives after
(in case of setup checking) or before (hold checking) it is required,
then we have a timing violation (negative slack). STA makes sure that a circuit
will correctly perform its function (yet it tells nothing about correctness of
that function)

:::{seealso}
Check out our [STA and timing closure guide](https://docs.google.com/document/d/13J1AY1zhzxur8vaFs3rRW9ZWX113rSDs63LezOOoXZ8/edit#heading=h.9y68197ebff7) for more in depth details.
:::

The default flow runs multiple `STA` `Step`(s) `OpenROAD.STAPostPNR` is the
final `STA` `Step` and the most important one to check.

Inside the `Step` folder there is a file called `summary.rpt` which summarizes
important metrics for each [IPVT](../../glossary.md#term-IPVT) [timing corner](../../glossary.md#term-timing-corner):

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
the log files and reports generated for each `IPVT corner`.

```text
45-openroad-stapostpnr/
└── nom_tt_025C_1v80/
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

TODO: NEXT SHOULDN'T BE MIGRATING FROM OPENLANE1?
