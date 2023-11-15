# Hardening Designs with the Default Flow

When you have OpenLane up and running, you can start using it to implement your
hardware designs.

Hardware designs are written in **hardware description languages**, which, as
the name implies, describe the hardware constructs in a manner similar to
programming languages, and designers then use tools like OpenLane to transform
these hardware expressions into a database format that is then sent to a foundry
for manufacturing.

Designs can either be **top-level chips** or **macros**. Top-level chips are,
as the name implies, full chips that are to be sent to a foundry for manufacture.

Macros, on the other hand, are "pre-compiled" pieces of hardware that are
intended for integration into larger designs.

If you're coming from a software development background, you may liken macros to
static libraries- they are already compiled, but are intended to be used in a 
larger program and are not entirely useful on their own.

In this document we will go through the hardening steps and discuss in some
detail what considerations should be made when hardening either macros or
top-level chips that do not use any macros.

## Base Requirements

You should start by setting the basic configuration file for your design.

You can configure any of the variables in these lists:

* [All Common Flow Variables](../reference/flow_config_vars.md#universal-flow-configuration-variables)
* [All PDK/SCL Variables](../reference/pdk_config_vars.md)
* The declared configuration variables of [the default Flow's steps](../reference/flow_config_vars.md#classic)
    * Click on each step to see its configuration variables.

The basic configuration `config.json` file for the default flow should at least
contain these variables:

* [`DESIGN_NAME`](../reference/flow_config_vars.md#DESIGN_NAME)
* [`VERILOG_FILES`](../reference/step_config_vars.md#Yosys.Synthesis.VERILOG_FILES)
* [`CLOCK_PORT`](../reference/flow_config_vars.md#CLOCK_PORT)
* [`DESIGN_IS_CORE`](../reference/flow_config_vars.md#DESIGN_IS_CORE)

So, for example:
    
```json
    "DESIGN_NAME": "spm",
    "VERILOG_FILES": "dir::src/*.v",
    "CLOCK_PORT": "clk",
    "DESIGN_IS_CORE": false
```

These configurations should get you through the flow with the all other
configurations using OpenLane default values, which you can read about here.
However, in the coming sections we will take a closer look on how to determine
the best values for most of the other configurations.

## Synthesis

Synthesis is the process by which RTL is transformed into logic primitives,
then again transformed into a list of "standard cells"- silicon patterns.

The default flow uses Yosys for Synthesis, namely,
[this step](../reference/step_config_vars.md#Yosys.Synthesis).

In general, there's not much to mess around with regards to
synthesis, but here are some tips for using a couple variables:

* If your macro is huge (200k+ cells), then you might want to try setting
  [`SYNTH_NO_FLAT`](../reference/step_config_vars.md#Yosys.Synthesis.SYNTH_NO_FLAT)
  to `1` (Tcl)/`true` (JSON), which will postpone the flattening of the design
  during synthesis until the very end.

## Static Timing Analysis

Static Timing Analysis happens multiple times during the flow, to ensure that
the timing constraints on the design are met:

* A **setup** violation: for when a clock edge arrives too early compared to
  the data it is intended to capture.
  * What this effectively means is that a design with a setup violation cannot
    run at its rated clock speed.
* A **hold** violation: for when data changes too quickly after the arrival of
  its capturing clock edge.
  * A design with hold violations is in most circumstances dead-on-arrival.

Here are some variables you need to consider:
* [`CLOCK_PORT`](../reference/flow_config_vars.md#CLOCK_PORT): Self-explanatory.
* [`CLOCK_PERIOD`](../reference/flow_config_vars.md#CLOCK_PERIOD): The value will
  be used to calculate any timing violations, and also in resizer stages, attempt
  to fix the cells in question. If the clock period could not be reasonably achieved,
* [`IO_DELAY_CONSTRAINT`](../reference/pdk_config_vars.md#IO_DELAY_CONSTRAINT)

You may also want to write a custom SDC file to be used in STA and CTS.
The default SDC file in the default flow is [this file](../../../openlane/scripts/base.sdc),
however, you can change that by pointing to a new file with the environment variable
[`FALLBACK_SDC_FILE`](../reference/step_config_vars.md#Misc.LoadBaseSDC.FALLBACK_SDC_FILE)

Currently, static timing analysis is done:

1. After synthesis, using the Verilog netlist and base SDC file.
1. After every repair or resizing step, namely:
    * `OpenROAD.RepairDesign` (after global placement)
    * `OpenROAD.ResizerTimingPostCTS` (after clock tree synthesis)
    * `OpenROAD.ResizerTimingPostGRT` (after global routing)
1. After detailed routing, using extracted parasitics.

## Floorplanning

Floorplanning refers to creating the first view of the design with physical
dimensions. At this stage, that is primarily:
* The die area: the total area of a macro or chip.
* The core area: the effective area used for cell placement, which is <= 

You have three options for floorplanning in the default flow:

1. Let the tools determine the area relative to the size and number of cells.
  * This is done by setting [`FP_SIZING`](../reference/step_config_vars.md#OpenROAD.Floorplan.FP_SIZING)
  to `relative` (the default value), and setting [`FP_CORE_UTIL`](../reference/step_config_vars.md#OpenROAD.Floorplan.FP_CORE_UTIL)
  as the core utilization percentage. You may also the aspect ratio
  (`1` by default) by changing [`FP_ASPECT_RATIO`](../reference/step_config_vars.md#OpenROAD.Floorplan.FP_ASPECT_RATIO).
2. Set a specific die area by setting [`FP_SIZING`](../reference/step_config_vars.md#OpenROAD.Floorplan.FP_SIZING)
  to `absolute` and setting the [`DIE_AREA` configuration variable](../reference/step_config_vars.md#OpenROAD.Floorplan.DIE_AREA).

<!--
1. Use a template DEF and apply the same dimensions of that DEF file.
  To use this option set
  [`FP_DEF_TEMPLATE`](../reference/step_config_vars.md#Odb.ApplyDEFTemplate) to
  point to that DEF file.

```{note}
Using `FP_DEF_TEMPLATE` will also copy the I/O Placement from the template DEF
file- not just the floorplan.
```
-->

## PDN Generation

You can find a full list of power distribution network configuration variables
in the PDN step [here](../reference/step_config_vars.md#power-distribution-network-generation).

Most designs would have to change these values based on the size of the floorplan:

* `FP_PDN_VPITCH`
* `FP_PDN_VSPACING`
* `FP_PDN_HPITCH`
* `FP_PDN_HSPACING`

A visualization of the values could be found below:

```{include} ./pdn.svg
:start-line: 2
```


## I/O Placement

I/O placement refers to finding the locations of the metal pins for the ports
of your design.

There are, once again, multiple methods to perform I/O placement in the default
flow:

1. Letting OpenROAD randomly assign IOs using the random equidistant mode.
   This is the default.
2. Manually setting the direction of each pin using a configuration file
   by pointing [`FP_PIN_ORDER_CFG`](../reference/step_config_vars.md#Odb.CustomIOPlacement.FP_PIN_ORDER_CFG)
   to point to that file.

<!--
1. As mentioned above, by using [`FP_DEF_TEMPLATE`](../reference/step_config_vars.md#Odb.ApplyDEFTemplate).
-->

## Placement

Placement is the act of placing the various design subcomponents- typically
standard cells- on the floorplan, typically with the goal of minimizing the
**total virtual wire length**.

The total virtual wire length is defined as the total distance of all virtual
wires connecting any two cells and/or cell and pin. Minimizing this is useful
for three reasons:
* Shorter wires are easier to route
* Shorter wires introduce less
  [parasitic values](https://en.wikipedia.org/wiki/Parasitic_element_(electrical_networks))
* Shorter wires are less susceptible to the
  [antenna effect](https://en.wikipedia.org/wiki/Antenna_effect)

Placement is done across two stages: "global placement" and "detailed placement".

### Global Placement
For a rundown of what global placement does, please see the Global Placement
step documentation [here](../reference/step_config_vars.md#OpenROAD.GlobalPlacement).

For global placement, the most important value would be
[`PL_TARGET_DENSITY_PCT`](../reference/step_config_vars.md#OpenROAD.GlobalPlacement.PL_TARGET_DENSITY_PCT)
which should be easy to set as follows:

- If your design is not a tiny design, then `PL_TARGET_DENSITY_PCT`
    should have a value that is `FP_CORE_UTIL` + ~10%.

- If your design is a tiny design, `PL_TARGET_DENSITY_PCT` should have high
  value, while `FP_CORE_UTIL` should have a low value.
  (i.e `PL_TARGET_DENSITY_PCT` set to 50 and `FP_CORE_UTIL` set to 5).
    - In very tiny designs the approximated DIE AREA in the floorplan stage may
    not leave enough room to insert tap cells in the design.
    Thus, it is recommended to use `FP_SIZING` as `absolute` and
    manually setting an appropriate `DIE_AREA`:
    check [the floorplan section](#floorplanning) for more details.
    You may also want to reduce the values for:
        * [`FP_PDN_HORIZONTAL_HALO`](../reference/step_config_vars.md#OpenROAD.GeneratePDN.FP_PDN_HORIZONTAL_HALO)
        * [`FP_PDN_VERTICAL_HALO`](../reference/step_config_vars.md#OpenROAD.GeneratePDN.FP_PDN_VERTICAL_HALO)

There is also [`GPL_CELL_PADDING`](../reference/step_config_vars.md#OpenROAD.GlobalPlacement.GPL_CELL_PADDING).
This will treat cells as "wider" than they are, which has an impact on routing
and diode insertion. If you increase the padding, make sure to recalculate the
`PL_TARGET_DENSITY_PCT` as such: {math}`util \approx FP\_CORE\_UTIL + 10 + 5 * GPL\_CELL\_PADDING`.

### Detailed Placement

For a rundown of what detailed placement does, please see the Detailed Placement
step documentation [here](../reference/step_config_vars.md#OpenROAD.DetailedPlacement).

The only value to consider here is the
[`DPL_CELL_PADDING`](../reference/step_config_vars.md#OpenROAD.GlobalPlacement.DPL_CELL_PADDING),
which must be less than or equal to the `DPL_CELL_PADDING` specified above.

## Clock Tree Synthesis

It's fine to leave values as defaults for clock tree synthesis most of the time:
see the step [`OpenROAD.CTS`](../reference/step_config_vars.md#OpenROAD.CTS) for
more info.

Clock tree synthesis takes some time compared to other steps you've encountered
so far.

<!--
TODO:
## Power Grid/Power Distribution Network
-->


## Routing

Most configurations here were optimized based on a large design set and are
best left as is.

Routing in general goes through these phases:

* **Global Routing**: Using [`OpenROAD.GlobalRouting`](../reference/step_config_vars.md#OpenROAD.GlobalRouting)
* **Detailed Routing**: Using [`OpenROAD.DetailedRouting`](../reference/step_config_vars.md#OpenROAD.DetailedRouting)

The subsections include some notes:

#### Antenna Mitigation
To help mitigate the antenna effect, after Global Placement there are also three
other steps you may choose to enable:

* [`Odb.DiodesOnPorts`](../reference/step_config_vars.md#Odb.DiodesOnPorts):
  Unconditionally inserts diodes on design ports. This is helpful for hardening
  macros, where you don't know how long the wires external to the macro are
  going to be. Requires {math}`GPL\_CELL\_PADDING \ge 2`.
* [`Odb.HeuristicDiodeInsertion`](../reference/step_config_vars.md#Odb.HeuristicDiodeInsertion):
  Inserts diodes based on the virtual wire length, s.t. nets longer than
  a specific threshold get a diode inserted by default. Disabled by default, but
  can be enabled by setting flow config variable `RUN_HEURISTIC_DIODE_INSERTION` to `true`.
  Requires {math}`GPL\_CELL\_PADDING \ge 2`.
* [`OpenROAD.RepairAntennas`](../reference/step_config_vars.md#OpenROAD.RepairAntennas):
  Uses a more advanced antenna repair algorithm built into OpenROAD. Enabled by
  default, can be disabled by setting flow config variable `RUN_ANTENNA_REPAIR`
  to `false`.


### `DRT_THREADS`

By default, detailed routing, which is the most computationally expensive step
in the flow, will use all available threads on your computer by default.
You can decrease that by overriding the step variable
[`DRT_THREADS`](../reference/step_config_vars.md#OpenROAD.DetailedRouting.DRT_THREADS).

Be advised that higher is always better for runtime.

## GDSII Streaming

After detailed routing, the LEF/DEF views are converted to GDSII. GDSII is the
final view, and it is the one submitted to foundries for manufacturing.

The default flow tapes out GDSII from LEF/DEF using two tools:
  * [Magic](http://opencircuitdesign.com/magic/): Using [`Magic.StreamOut`](../reference/step_config_vars.md#Magic.StreamOut)
  * [KLayout](http://klayout.de): Using [`KLayout.StreamOut`](../reference/step_config_vars.md#KLayout.StreamOut)

The idea is, if there's any difference between the two GDSII views, one tool
is misconfigured or the LEF/DEF contains some ambiguity: at any rate, the design
may not be suitable for manufacturing. If your design exhibits differences between
the two, please [file an issue](https://github.com/efabless/openlane2/issues/new)
and we will investigate.

The difference is a simple geometric XOR run using KLayout,
using the [`KLayout.XOR` step](../reference/step_config_vars.md#KLayout.XOR).

If the PDK does not support one of the two tools, that tool will not run, and
attempting the XOR may interrupt the flow: it is thus a good idea to set
[`RUN_KLAYOUT_XOR`](../reference/step_config_vars.md#Layout.XOR.RUN_KLAYOUT_XOR)
to `false`.

## Signoff

The final part of the flow is running a series of geometric, logical and
electrical checks on the final design.

### Design Rule Checking

Design Rule Checking (DRC) is done using Magic, specifically the [`Magic.DRC` step](../reference/step_config_vars.md#Magic.DRC).

Designs with design rule violations are not accepted for manufacturing by any foundry.

You can control whether the DRC should be done on at the GDSII level or at the
LEF/DEF level. We recommend using LEF/DEF for smaller designs and macros, and
LEF/DEF in all other cases:

* GDS is more concrete, but as such, checks take far longer the LEF/DEF.
* LEF/DEF is more abstract, however, that can result in false-positives in some
  designs.

You can specify your favored method using the config var
[`MAGIC_DRC_USE_GDS`](../reference/step_config_vars.md#Magic.DRC.MAGIC_DRC_USE_GDS).

If your LEF/DEF DRC fails, it is recommended to run the `GDS` check as well just
to verify that it's not abstraction issue; you can do this as follows:

```sh
python3 -m openlane <config file> --last-run --from magic.drc --to magic.drc -c MAGIC_DRC_USE_GDS=true
```

If you find an inconsistency, please [file an issue](https://github.com/efabless/openlane2/issues/new)
and we will investigate.

### SPICE Extraction + Layout vs. Schematic

Layout vs. Schematic (LVS) is done on a SPICE netlist extracted from the GDSII by Magic
vs. a Verilog netlist exported from the layout by OpenROAD.

It verifies the following:
  * There are no unexpected shorts in the final layout.
  * There are no unexpected opens in the final layout.
  * All signals are connected correctly.

The SPICE extraction is done using [this step](../reference/step_config_vars.md#Magic.SpiceExtraction),
and the LVS extraction is done using [this one](../reference/step_config_vars.md#Magic.LVS).

```{note}
Like GDS, the variable [`MAGIC_EXT_USE_GDS`](../reference/step_config_vars.md#Magic.SpiceExtraction.MAGIC_EXT_USE_GDS),
and the same consideration applies. Use your best judgment.
```

## Done!
If all works out, you've just hardened your first chip.

The final views can be found under `<run-path>/final`.

You can learn how to integrate macros into top level chips in the next page.