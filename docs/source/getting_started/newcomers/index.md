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
   {term}`Nix` and setup {term}`cachix`.

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
   This also downloads {term}`sky130` {term}`PDK`.

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

This is the source {term}`RTL` of the design.

:::{dropdown} spm.v

```{literalinclude} ../../../../openlane/examples/spm/src/spm.v
:language: verilog
```

:::

#### Configuration

Designs in OpenLane have configuration files. A configuration file contains
{term}`Variable`(s). With them you control the OpenLane flow
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
Check out {doc}`../../reference/step_config_vars` and {doc}`../../reference/flows`
for all available {term}`Variable`(s)
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

### Results of SPM as core ?

#### Viewing the Layout

To open the final {term}`GDSII` layout run this command:

```console
[nix-shell:~/openlane2]$ openlane --last-run --flow openinklayout ~/my_designs/spm/config.json
```

This opens {term}`KLayout` and you should be able to see the following:

```{figure} ./spm-gds.png
:align: center

```

If you wish to use {term}`OpenROAD` GUI use the following:

```console
[nix-shell:~/openlane2]$ openlane --last-run --flow openinopenroad ~/my_designs/spm/config.json
```

---

#### Run folder

A new **run folder** (named something like `runs/RUN_2023-12-27_16-59-15`)
should have been created.

By default, OpenLane runs a {term}`Flow` composed of a
sequence of {term}`Step`(s).
Each `Step` has its separate folder.

For example, the `OpenROAD.TapEndCapInsertion` `Step` creates the following
folder `14-openroad-tapendcapinsertion` which would be inside the run folder.

A `Step` folder has log files, report files, {term}`Metrics`
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
- `state_in.json`: contains a dictionary of design layout formats (such as `DEF`
  file) and design `Metrics` available as inputs to a `Step` .
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

#### Viewing Intermediate Layout

Additionally, you can view the intermediate layout at each `Step`:

```console
[nix-shell:~/openlane2]$ openlane --last-run --flow openinklayout ~/my_designs/spm/config.json --with-initial-state ~/my_designs/spm/runs/RUN_2023-12-27_16-59-15/14-openroad-tapendcapinsertion/state_out.json"
```

#### Final Results

Inside the run folder, there is a folder called `final`. This folder contains
other folders that contains all the different layout views produced by the flow
such as {term}`DEF` and {term}`LEF`.
{term}`GDSII` and others. It looks like this:

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
final `metrics` in `JSON` and {term}`CSV` formats.

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

`DRC` stands for Design Rule Checking which are set by the FOUNDRY/Chip Manufacturer?
rules that the layout has to satisfy in order to be manufacturable.
Such as, checking for minimum allowed spacing between two `met1` shapes.

OpenLane runs two `DRC` steps using `Magic` and `KLayout`: `Magic.DRC` and
`KLayout.DRC`. The Layout and `PDK` [DRC deck] are inputted to the tools running
DRC, as shown in the diagram bellow:

```{figure} ./OL-DRC.png
:align: center
:scale: 50 %

DRC (Design Rule Checking) Flow
```

If `DRC` errors are found OpenLane will generate an error reporting
the total count of violations found by each `Step`.

To view `DRC` errors graphically. Open the layout:

```console
[nix-shell:~/openlane2]$ openlane --last-run --flow openinklayout ~/my_designs/spm/config.json
```

Then in the menu bar select Tools -> Marker Browser. A new window should open.

```{figure} ./klayout-markerbrowser-menu.png
:align: center
```

Then select File -> open and then select the report file you would like to open.
Report files will be found under `52-magic-drc/reports/drc.klayout.xml` and
`53-klayout-drc/report/drc.klayout.xml`

:::{tip}
The initial number in `53-klayout-drc` (`53`) may vary according to a design configuration.
:::

```{figure} ./klayout-markerbrowser-menu-2.png
:align: center
```

#### LVS

`LVS` stands for Layout Versus Schematic. It compares the layout {term}`GDSII` or
`DEF`/`LEF`, with the schematic which is usually in
{term}`Verilog` ensuring that connectivity in both
views are matching. Sometimes, user configuration or even the tools have errors
and such check is important to catch them.

Common `LVS` errors include but are not limited to:

- Shorts: Two or more wires that should not be connected have been and must be
  separated. The most problematic is power and ground shorts.
- Opens: Wires or components that should be connected are left dangling or only
  partially connected. These must be connected properly.
- Missing Components: An expected component has been left out of the layout.

`Netgen.LVS` is the `Step` ran for `LVS` using a tool called
{term}`Netgen`. First, the layout is converted to
{term}`SPICE netlist`. Next
the layout and the schematic are inputted to Netgen, as shown in the diagram
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
important metrics for each {term}`IPVT` {term}`timing corner`:

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
  6. Checks the `SDC` for combinationals loops, register/latch with multiple clocks
     or no clocks, ports missing input delay and generated clocks
  7. Worst setup or hold violating path

---

### SPM as a macro for [Caravel](https://caravel-harness.readthedocs.io/en/latest/)

Often a design by itself serves no purpose unless interfaced with and/or integrated
into another design or a chip. We are going to harden `spm` design again but
this time we will have it as a [Caravel User Project Wrapper](https://caravel-user-project.readthedocs.io/en/latest/))
macro for the chip [Caravel](https://caravel-harness.readthedocs.io/en/latest/)

:::{admonition} About Caravel
:class: seealso

The Efabless Caravel chip is a ready-to-use test harness for creating designs
with the Google/Skywater 130nm Open PDK. The Caravel harness comprises of base
functions supporting IO, power and configuration as well as drop-in modules for
a management SoC core, and an approximately 3000um x 3600um open project area
for the placement of user IP blocks.

Check [Caravel](https://caravel-harness.readthedocs.io/en/latest/) for more information.
:::

#### RTL updates

We begin by updating the `RTL` needed for integration of the spm into `Caravel`.

1. Create a new folder `~/my_designs/spm-user_project_wrapper/` and

   ```console
   [nix-shell:~/openlane2]$ mkdir -p ~/my_designs/spm-user_project_wrapper
   ```

2. Add the following new `RTL` to `~/my_designs/spm-user_project_wrapper/SPM_example.v`:

   :::{dropdown} SPM_example.v

   ```{literalinclude} ../../../../openlane/examples/spm-user_project_wrapper/SPM_example.v

   ```

   :::

3. Also add `~/my_designs/spm-user_project_wrapper/user_project_wrapper.v`:

   :::{dropdown} user_project_wrapper

   ```{literalinclude} ../../../../openlane/examples/spm-user_project_wrapper/user_project_wrapper.v

   ```

   :::

4. Finally, we need an additional file
   `~/my_designs/spm-user_project_wrapper/defines.v` which is required
   by `Caravel User Project`.

   :::{dropdown} defines.v

   ```{literalinclude} ../../../../openlane/examples/spm-user_project_wrapper/defines.v

   ```

   :::

:::{seealso}
Checkout [Caravel User Project#Verilog Integration](https://caravel-user-project.readthedocs.io/en/latest/#verilog-integration)
for information about the `RTL` changes.
:::

(configuration-user-project-wrapper)=

#### Configuration

Then we need to create a configuration file to pass to the flow.

- First, create a template configuration `JSON` file:

  ```console
  TODO: insert command here
  ```

- Then Update the configuration as follows.

  1. Update the variable `DESIGN_NAME` to match our top level module in the `RTL`:

     ```json
     {
       "DESIGN_NAME": "user_project_wrapper"
     }
     ```

  2. Point to the new `RTL` files using the variable `VERILOG_FILES`

     ```json
     {
       "DESIGN_NAME": "user_project_wrapper",
       "VERILOG_FILES": [
         "dir::./defines.v",
         "dir::./SPM_example.v",
         "dir::./user_project_wrapper.v"
       ]
     }
     ```

  3. Match the clock frequency set by `Caravel` chip by modifying the
     variable `CLOCK_PERIOD`:

     ```json
     {
       "DESIGN_NAME": "user_project_wrapper",
       "VERILOG_FILES": [
         "dir::./defines.v",
         "dir::./SPM_example.v",
         "dir::./user_project_wrapper.v"
       ]
       "CLOCK_PERIOD": 25
     }
     ```

  4. The design has a new IO interface now so we need to update `CLOCK_PORT` in
     order to generate a proper clock tree.

     ```json
     {
       "DESIGN_NAME": "user_project_wrapper",
       "VERILOG_FILES": [
         "dir::./defines.v",
         "dir::./SPM_example.v",
         "dir::./user_project_wrapper.v"
       ],
       "CLOCK_PERIOD": 25,
       "CLOCK_PORT": "wb_clk_i"
     }
     ```

#### Running the flow

Lets try running the flow:

```console
[nix-shell:~/openlane2]$ openlane ~/my_designs/spm-user_project_wrapper/config.json
```

#### Addressing issues

The flow will fail with the following message:

```text
[ERROR PPL-0024] Number of IO pins (637) exceeds maximum number of available positions (220).
Error: ioplacer.tcl, 56 PPL-0024
```

The reason that happens is that when we change the `RTL` of the design we
changed the IO pin interface of the design to match the interface needed by
`Caravel User Project Wrapper`.

`Caravel User Project Wrapper` needs lot of IO pins. By default, the flow will attempt
create a floorplan using a utilization of 50%. Relative to the cells in the design,
there are too many IO pins to fit in such a floorplan.

This can be solved by setting a lower utilization value. You will find out that
about 5% utilization is needed for the floorplan to succeed. This is
controlled by `FP_CORE_UTIL` {term}`Variable`.

Update the configuration as follows:

```json
{
  "DESIGN_NAME": "user_project_wrapper",
  "CLOCK_PERIOD": 25,
  "CLOCK_PORT": "wb_clk_i",
  "VERILOG_FILES": [
    "dir::./defines.v",
    "dir::./SPM_example.v",
    "dir::./user_project_wrapper.v"
  ],
  "FP_CORE_UTIL": 5
}
```

Then run the flow again:

```console
[nix-shell:~/openlane2]$ openlane ~/my_designs/spm-user_project_wrapper/config.json
```

#### Examining the results

Let's view the layout:

```console
[nix-shell:~/openlane2]$ openlane --last-run --flow openinklayout ~/my_designs/spm-user_project_wrapper/config.json
```

```{figure} ./spm-caravel-user-project-util.png

SPM with 5% utilization
```

:::{tip}
You can control the visible layers in KLayout by right clicking in the layers
area and selecting hide all layers. Then double click on the layers that you want
to view. In this figure, only `met2.pin`, `met3.pin` and `prBoundary.boundary`
are shown.
:::

As shown above, the are a lot of pins needed by the design and
certainly a floorplan with 50% utilization wouldn't fit all the pins.

---

#### Caravel Integration

`Caravel User Project Wrapper` is a macro inside `Caravel`. To be able to use
any design as a `Caravel User Project Wrapper` it has to match the footprint
that `Caravel` is expecting so we can't rely on `FP_CORE_UTIL`.

##### IO Pins

The top level design `Caravel` is expecting any `Caravel User Project Wrapper`
to have the IO pins at specific locations and with specific dimensions. We
can achieve that by using the variable `FP_DEF_TEMPLATE`. `FP_DEF_TEMPLATE` is a
`DEF` file used as a template for the design's floorplan. IO pins shapes and
locations are copied from the template `DEF` file over to our design. In addition,
the same die area is used as the one in the template `DEF` file.

Save this file [template.def](../../../../openlane/examples/spm-user_project_wrapper/template.def),
in your design's directory which should be `~/my_designs/spm-user_project_wrapper/`.
Then update the design's configuration by adding `FP_DEF_TEMPLATE` variable:

```json
{
  "DESIGN_NAME": "SPM_example",
  "VERILOG_FILES": ["dir::./defines.v", "dir::./SPM_example.v"]
  "CLOCK_PERIOD": 25,
  "CLOCK_PORT": "wb_clk_i",
  "FP_DEF_TEMPLATE": "dir::./template.def",
  "FP_SIZING": "absolute",
  "DIE_AREA": [0, 0, 2920, 3520]
}
```

##### Power Distribution Network (PDN)

A macro's Power Distribution Network (`PDN`) is responsible for the delivery of
power to cells in the design. A macro's internal `PDN` is exposed through pins
as an interface for integration with another designs. These pins are similar to
data IO pins but often much larger.

Here is another an example of a macro that is fully integrated inside `Caravel`:

```{figure} ./caravel-1.png
:align: center

Example of a macro integrated inside Caravel
```

This figure displays `Caravel` chip. The highlighted rectangle is where
`Caravel User Project Wrapper` is. Let's zoom in at the top right corner of
this area.

```{figure} ./caravel-pdn-2.png
:align: center

Top right corner of macro integrated inside Caravel
```

As highlighted there are power rings surrounding our wrapper. connectivity
between the wrapper rings and the chip is done through the highlighted light blue
`met3` wires.

Our `PDN` of `Caravel User Project Wrapper` has to be configured to look like the
figure shown above. This is done by using a collection of variables which are responsible
for controlling the shape, location and metal layers of the `PDN` pins offering
the power interface of the macro.

Append the following variables to your configuration:

```json
    "FP_PDN_CORE_RING": 1,
    "FP_PDN_CORE_RING_VWIDTH": 3.1,
    "FP_PDN_CORE_RING_HWIDTH": 3.1,
    "FP_PDN_CORE_RING_VOFFSET": 12.45,
    "FP_PDN_CORE_RING_HOFFSET": 12.45,
    "FP_PDN_CORE_RING_VSPACING": 1.7,
    "FP_PDN_CORE_RING_HSPACING": 1.7,
    "FP_PDN_VWIDTH": 3.1,
    "FP_PDN_HWIDTH": 3.1,
    "FP_PDN_VSPACING": "expr::(5 * $FP_PDN_CORE_RING_VWIDTH)",
    "FP_PDN_HSPACING": "expr::(5 * $FP_PDN_CORE_RING_HWIDTH)",
```

:::{seealso}
Visit [`OpenROAD.GeneratePDN`](#step-openroad-generatepdn) for more information
about each of the above variables
:::

`Caravel` is a chip with multiple power domains. We need to match these domains
in our configuration by updating `VDD_NETS` and `GND_NETS` variables:

```json
    "VDD_NETS": [
        "vccd1",
        "vccd2",
        "vdda1",
        "vdda2"
    ],
    "GND_NETS": [
        "vssd1",
        "vssd2",
        "vssa1",
        "vssa2"
    ]
```

##### Timing Constraints

TODO: Insert a paragraph here describing user project wrapper SDC
