> Note: Information in this document is still being ported from OpenLane 1 to OpenLane 2 and may be partially inaccurate.
# Multi-Macro Top Level Chips
The current methodology views a multi-macro top-level chip using the following hierarchy:

- Chip Core
    - Macros
    - Rest of the Design
- Chip IO
    - IO Pads
    - Power Pads
    - Corner Pads

The current methodology goes as follows:
1. Hardening the hard macros.
2. Hardening the core with the hard macros inside it.
3. Hardening the padframe
4. Hardening the full chip with the padframe.

You already know how to harden individual macros from the previous document. Now, a couple are left.
## Hardening The Core

The chip core would usually have other macros inside it.

You need to set the following environment variables in your configuration file for the chip core:

* [`VERILOG_FILES`](../reference/step_config_vars.md#Yosys.Synthesis.VERILOG_FILES)
    * If you're using standard cells directly in your RTL, [`SYNTH_READ_BLACKBOX_LIB`](../reference/step_config_vars.md#Yosys.Synthesis.SYNTH_READ_BLACKBOX_LIB)
* [`EXTRA_LIBS`](../reference/flow_config_vars.md#EXTRA_LIBS)
* [`EXTRA_LEFS`](../reference/flow_config_vars.md#EXTRA_LEFS)
* [`EXTRA_VERILOG_MODELS`](../reference/flow_config_vars.md#EXTRA_VERILOG_MODELS)
* [`EXTRA_GDS_FILES`](../reference/flow_config_vars.md#EXTRA_GDS_FILES)

You also need to enable the [`Odb.ManualMacroPlacement`](../reference/step_config_vars.md#manual-macro-placement) step.
* In the default flow, you use it by creating a placement configuration file and pointing to it using this variable: [`MACRO_PLACEMENT_CFG`](../reference/step_config_vars.md#Odb.ManualMacroPlacement.MACRO_PLACEMENT_CFG)
## Hardening the Padframe

(TODO)