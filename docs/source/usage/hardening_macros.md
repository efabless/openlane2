> Note: Information in this document is still being ported from OpenLane 1 to OpenLane 2 and may be partially inaccurate.
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

The basic configuration `config.json` file for the default flowshould at least
contain these variables:

* [`DESIGN_NAME`](../reference/flow_config_vars.md#DESIGN_NAME)
* [`VERILOG_FILES`](../reference/step_config_vars.md#Yosys.Synthesis.VERILOG_FILES)
* [`CLOCK_PORT`](../reference/flow_config_vars.md#DESIGN_NAME)
* [`DESIGN_IS_CORE`](../reference/flow_config_vars.md#DESIGN_IS_CORE)

So, for example:
    
```json
    "DESIGN_NAME": "spm",
    "VERILOG_FILES": "dir::src/*.v",
    "CLOCK_PORT": "clk",
    "DESIGN_IS_CORE": false
```

These configurations should get you through the flow with the all other configurations using OpenLane default values, which you can read about here. However, in the coming sections we will take a closer look on how to determine the best values for most of the other configurations.

## Synthesis
Then you need to consider the best values for the `MAX_FANOUT_CONSTRAINT`.

If your macro is huge (200k+ cells), then you might want to try setting `SYNTH_NO_FLAT` to `1` (Tcl)/`true` (JSON), which will postpone the flattening of the design during synthesis until the very end.

Other configurations like `SYNTH_SIZING`, `SYNTH_BUFFERING`, and other synthesis configurations do not have to be changed. However, the advanced user can check [this][0] documentation for more details about those configurations and their values.

## Static Timing Analysis

Static Timing Analysis happens multiple times during the flow. However, they all use the same base.sdc file. You can control the outcome of the static timing analysis by setting those values:

1. The clock ports in the design, explained in the base requirements section `CLOCK_PORT`.

2. The clock period that you prefer the design to run with. This could be set using `CLOCK_PERIOD` and the unit is ns. It is important to note that the flow will use this value to calculate the worst and total negative slack, also if timing optimizations are enabled, it will try to optimize for it and give suggested clock period at the end of the run in `<run-path>/reports/metrics.csv` This value should be used in the future to speed up the optimization process and it will be the estimated value at which the design should run.

3. The IO delay percentage from the clock period `IO_DELAY_CONSTRAINT`. More about that [here][0].

4. You may want to write a custom SDC file to be used in STA and CTS. The default SDC file in the flow is [this file][11]. However, you can change that by pointing to a new file with the environment variable `BASE_SDC_FILE`. More about that [here][0].

Other values are set based on the (PDK, STD_CELL_LIBRARY) used. You can read more about those configurations [here][0].

Static Timing Analysis are done after:

1. Synthesis using the verilog netlist.

2. Placement using OpenROAD's estimate_parasitics.

3. Timing optimizations using the verilog netlist.

4. Global Routing using OpenROAD's estimate_parasitics.

5. Detailed Routing using SPEF extraction and the verilog netlist.

For SPEF extraction, you can control the wire model and the edge capacitance factor through these variables `SPEF_WIRE_MODEL` and `SPEF_EDGE_CAP_FACTOR`.

More about that [here][0].

## Floorplan

During Floor plan, you have one of three options:

1. Let the tools determine the area relative to the size and number of cells. This is done by setting `FP_SIZING` to `relative` (the default value), and setting `FP_CORE_UTIL` as the core utilization percentage. Also, you can change the aspect ratio by changing `FP_ASPECT_RATIO`.

2. Set a specific DIE AREA by making `FP_SIZING` set to `absolute` and then giving the size as four coordinates to `DIE_AREA`.

3. Use a template DEF and apply the same DIE AREA and dimensions of that DEF. Note that this option will also force the flow to use the same PIN locations and PIN names (they are copied over from the template DEF). To use this option set: `FP_DEF_TEMPLATE` to point to that DEF file.

You can read more about how to control these variables [here][0].


## IO Placement

For IO placement, you currently have four options:

1. Using a template DEF file and applying the same PIN locations and PIN names (they are copied over from the template DEF). Note that this will force the flow to apply the same exact DIE AREA and dimensions of the template DEF. To use that option set: `FP_DEF_TEMPLATE` to point to that DEF file.

2. Manually setting the direction of each pin using a configuration file such as [this one][7]. Then you need to set `FP_PIN_ORDER_CFG` to point to that file.

3. Using contextualized pin placement, which will automatically optimize the placement of the pins based on their context in the larger design that includes them. This relevant for macros since they will be included inside a core, and also relevant for the core since it will be part of a bigger chip. For this to happen, you need to point to the LEF and DEF of the container/parent design using these two variables: `FP_CONTEXT_DEF` and `FP_CONTEXT_LEF`. Note that currently this script can only handle the existance of a single instance of that macro.

4. To let the tool randomly assign IOs using the random equidistant mode. This is the default way.

The options are prioritized based on the order mentioned above. This means that if you set a value for `FP_DEF_TEMPLATE` it will be used and the rest - if they exist - will be ignored.

You can read more about those configurations [here][0].

## Placement

Placement is done in three steps: Global Placement, Optimizations, and Detailed Placement.

### Global Placement

For Global Placement, the most important value would be `PL_TARGET_DENSITY_PCT` which should be easy to set.

- If your design is not a tiny design, then `PL_TARGET_DENSITY_PCT` should have a value that is `FP_CORE_UTIL` + 1~5%.

- If your design is a tiny design, `PL_TARGET_DENSITY_PCT` should have high value, while `FP_CORE_UTIL` should have a low value. (i.e `PL_TARGET_DENSITY_PCT` set to 50 and `FP_CORE_UTIL` set to 5). In very tiny designs (i.e. 1 std cell designs), the approximated DIE AREA in the floorplan stage may not leave enough room to insert tap cells in the design. Thus, it is recommended to use `FP_SIZING` as `absolute` and manually setting an appropriate `DIE_AREA`, check [the floorplan section](#floorplan) for more details. You may also want to reduce the values for `FP_PDN_HORIZONTAL_HALO` and `FP_PDN_VERTICAL_HALO`. You can read more about those [here][0].

Other values to be considered include `PL_SKIP_INITIAL_PLACEMENT`, you can read more about those [here][0].

### Detailed Placement

The only value to consider here is the `DPL_CELL_PADDING` which is usually selected for each (PDK,STD_CELL_LIBRARY) and should mostly be left as is. However, typically for the skywater libraries the value should be 4~6.

You can read more about that [here][0].

## Clock Tree Synthesis

Most of the values for clock tree synthesis are (PDK, STD_CELL_LIBRARY) specific and you can read more about those [here](../reference/pdk_config_vars.md).

You can disable it by setting `CLOCK_TREE_SYNTH` to `0`.

If you do not want all the clock ports to be used in clock tree synthesis, then you can use set `CLOCK_NET` to specify those ports. Otherwise, `CLOCK_NET` will be defaulted to the value of `CLOCK_PORT`.

## Power Grid/Power Distribution Network
See [here][9].

## Diode Insertion

Here, you have four options to choose from and they are controlled by setting `DIODE_INSERTION_STRATEGY` to one of the following values: (0, 1, 2, 3, 4, 5)

0. No diode insertion is done.

1. A diode is inserted for each PIN and connected to it.

2. A fake diode is inserted for each PIN and connected to it, then after an antenna check is run and the fake diodes are replaced with real ones if the pin is violated.

3. Rely on OpenROAD:FastRoute antenna avoidance flow to insert the diodes during global routing by using the Antenna Rule Checker and fixing violations. You can execute this iteratively by setting `GRT_MAX_DIODE_INS_ITERS`, it is capable to detect any divergence, so, you will probably end up with the lowest # of Antenna violations possible.

4. A smarter version of strategy 1 that attempts to reduce the number of inserted diodes and places a diode at each design pin.

5. A variant of 2 utilizing the script used in strategy 4.

You can read more about those configurations [here][0].

## Routing

The configurations here were optimized based on a large design set and are best left as is, however the advanced user could refer to [this documentation][0] to learn more about each used configuration and how to change it.

You are advised to change `ROUTING_CORES` based on your CPU capacity to specify the number of threads that TritonRoute can run with to perform Detailed Routing in the least runtime possible.

## GDS Streaming

The configurations here were selected based on a large design test set and the consulation of the magic sources; therefore they are best left as is. However, for the curious user, refer to [this documentation][0] to learn more about each used configuration and how to change it.

## Final Reports and Checks

Finally, the flow ends with physical verification. This begins by streaming out the GDS followed by running DRC, LVS, and Antenna checks on the design. Then, it produces a final summary report in csv format to summarize all the reports.

You can control whether the magic DRC should be done on GDSII or on LEF/DEF abstract views. We recommend using GDSII on macros while using LEF/DEF on the chip level. This should speed up the run process and still give results as accurate as possible. This is controlled by `MAGIC_DRC_USE_GDS`.

You can run Antenna Checks using OpenROAD ARC or magic. This is controlled by `USE_ARC_ANTENNA_CHECK`. The magic antenna checker was more reliable at the time of writing this documentation but it comes with a huge runtime trade-off and the accuracy gain is not significant enough to accept that tradeoff; thus, the default is OpenROAD's ARC.

You can control whether LVS should be run down to the device level or the cell level based on the type of the extraction. If you perform extraction on GDSII then it is going to be down to the device/transistor level, otherwise using the LEF/DEF views then it is going to be down to the cell/block level. This is controlled by `MAGIC_EXT_USE_GDS`.

You can enable LEC on the different netlists by setting `LEC_ENABLE` to one, which should run logic verification after writing each intermediate netlist.

The final GDSII file can be found under `<run-path>/final/gds`.

To integrate that macro into a core or a chip, check this [documentation on chip integration][4].

[0]: ../reference/configuration.md
[1]: ../reference/openlane_commands.md
[3]: https://github.com/The-OpenROAD-Project/OpenROAD/blob/master/src/pdn/doc/PDN.md
[4]: ./chip_integration.md
[5]: ./designs.md
[6]: ./exploration_script.md
[7]: https://github.com/The-OpenROAD-Project/openlane/blob/master/designs/spm/pin_order.cfg
[8]: ../for_developers/pdk_structure.md
[9]: ./advanced_power_grid_control.md
[10]: ../reference/datapoint_definitions.md
[11]: ./../../../scripts/base.sdc
