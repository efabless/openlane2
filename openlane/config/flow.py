# Copyright 2023 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os

from decimal import Decimal
from typing import List, Optional, Dict, Union

from .variable import Variable, Macro
from ..common import Path, get_script_dir


pdk_variables = [
    # Core/Common
    Variable(
        "STD_CELL_LIBRARY",
        str,
        "Specifies the default standard cell library to be used under the specified PDK.",
        pdk=True,
    ),
    Variable(
        "VDD_PIN",
        str,
        "The power pin for the cells.",
        pdk=True,
    ),
    Variable(
        "VDD_PIN_VOLTAGE",
        Decimal,
        "The voltage of the VDD pin.",
        pdk=True,
    ),
    Variable(
        "GND_PIN",
        str,
        "The ground pin for the cells.",
        pdk=True,
    ),
    Variable(
        "WIRE_LENGTH_THRESHOLD",
        Optional[Decimal],
        "A value above which wire lengths generate warnings.",
        units="µm",
        pdk=True,
    ),
    Variable(
        "TECH_LEFS",
        Dict[str, Path],
        "Map of corner patterns to to technology LEF files. A corner not matched here will not be supported by OpenRCX in the default flow.",
        pdk=True,
    ),
    Variable(
        "GPIO_PADS_LEF",
        Optional[List[Path]],
        "Path(s) to GPIO pad LEF file(s).",
        pdk=True,
    ),
    Variable(
        "GPIO_PADS_LEF_CORE_SIDE",
        Optional[List[Path]],
        "Path(s) to GPIO pad LEF file(s) as used for routing (?).",
        pdk=True,
    ),
    Variable(
        "GPIO_PADS_VERILOG",
        Optional[List[Path]],
        "Path(s) to GPIO pad Verilog models.",
        pdk=True,
    ),
    Variable(
        "GPIO_PADS_PREFIX",
        Optional[List[str]],
        "A list of pad cell name prefixes.",
        pdk=True,
    ),
    Variable(
        "PRIMARY_SIGNOFF_TOOL",
        str,
        "Specify the primary signoff tool for taping out with this PDK. For most open-source PDKs, that would be 'magic'.",
        pdk=True,
    ),
    # Timing and Power
    Variable(
        "DEFAULT_MAX_TRAN",
        Optional[Decimal],
        "Defines the default maximum transition value used in Synthesis and CTS.\nA minimum of 0.1 * CLOCK_PERIOD and this variable, if defined, is used.",
        units="ns",
        pdk=True,
    ),
    Variable(
        "DATA_WIRE_RC_LAYER",
        Optional[str],
        "A metal layer with which to estimate parasitics for data nets in earlier stages of the flow.",
        pdk=True,
        deprecated_names=["WIRE_RC_LAYER"],
    ),
    Variable(
        "CLOCK_WIRE_RC_LAYER",
        Optional[str],
        "A metal layer with which to estimate parasitics for clock nets in earlier stages of the flow.",
        pdk=True,
    ),
    Variable(
        "DEFAULT_CORNER",
        str,
        "The interconnect/process/voltage/temperature corner (IPVT) to use the characterized lib files compatible with by default.",
        pdk=True,
    ),
    Variable(
        "STA_CORNERS",
        List[str],
        "A list of fully qualified IPVT (Interconnect, transistor Process, Voltage, and Temperature) timing corners on which to conduct multi-corner static timing analysis.",
        pdk=True,
    ),
    # Floorplanning
    Variable(
        "FP_TRACKS_INFO",
        Path,
        "A path to the a classic OpenROAD `.tracks` file. Used by the floorplanner to generate tracks.",
        deprecated_names=["TRACKS_INFO_FILE"],
        pdk=True,
    ),
    Variable(
        "FP_TAPCELL_DIST",
        Decimal,
        "The distance between tap cell columns.",
        units="µm",
        pdk=True,
    ),
    Variable(
        "FP_IO_HLAYER",
        str,
        "The metal layer on which to place horizontal IO pins, i.e., the top and bottom of the die.",
        pdk=True,
    ),
    Variable(
        "FP_IO_VLAYER",
        str,
        "The metal layer on which to place vertial IO pins, i.e., the top and bottom of the die.",
        pdk=True,
    ),
    Variable("RT_MIN_LAYER", str, "The lowest metal layer to route on.", pdk=True),
    Variable("RT_MAX_LAYER", str, "The highest metal layer to route on.", pdk=True),
]

scl_variables = [
    # Common
    Variable(
        "SCL_GROUND_PINS",
        List[str],
        "SCL-specific ground pins",
        deprecated_names=["STD_CELL_GROUND_PINS"],
        pdk=True,
    ),
    Variable(
        "SCL_POWER_PINS",
        List[str],
        "SCL-specific power pins",
        deprecated_names=["STD_CELL_POWER_PINS"],
        pdk=True,
    ),
    Variable(
        "FILL_CELL",
        List[str],
        "A list of cell names or wildcards of fill cells to be used in fill insertion.",
        pdk=True,
    ),
    Variable(
        "DECAP_CELL",
        List[str],
        "A list of cell names or wildcards of decap cells to be used in fill insertion.",
        pdk=True,
    ),
    Variable(
        "LIB",
        Dict[str, List[Path]],
        "A map from corner patterns to a list of associated liberty files. Exactly one entry must match the `DEFAULT_CORNER`.",
        pdk=True,
    ),
    Variable(
        "CELL_LEFS",
        List[Path],
        "Path(s) to the cells' LEF file(s).",
        deprecated_names=["CELLS_LEF"],
        pdk=True,
    ),
    Variable(
        "CELL_GDS",
        List[Path],
        "Path(s) to the cells' GDSII file(s).",
        deprecated_names=["GDS_FILES", "CELLS_GDS"],
        pdk=True,
    ),
    Variable(
        "CELL_VERILOG_MODELS",
        Optional[List[Path]],
        "Path(s) to cells' Verilog model(s)",
        pdk=True,
    ),
    Variable(
        "CELL_BB_VERILOG_MODELS",
        Optional[List[Path]],
        "Path(s) to cells' black-box Verilog model(s)",
        pdk=True,
    ),
    Variable(
        "CELL_SPICE_MODELS",
        Optional[List[Path]],
        "Path(s) to cells' SPICE model(s)",
        pdk=True,
    ),
    Variable(
        "SYNTH_EXCLUSION_CELL_LIST",
        Path,
        "Path to a text file containing a list of cells to be excluded from the lib file in synthesis alone. If not defined, the original lib file will be used as-is.",
        deprecated_names=["NO_SYNTH_CELL_LIST"],
        pdk=True,
    ),
    Variable(
        "PNR_EXCLUSION_CELL_LIST",
        Path,
        "Path to a text file containing a list of undesirable or bad (DRC-failed or complex pinout) cells to be excluded from synthesis AND PnR. If not defined, all cells will be used.",
        deprecated_names=["DRC_EXCLUDE_CELL_LIST"],
        pdk=True,
    ),
    # Constraints
    Variable(
        "OUTPUT_CAP_LOAD",
        Decimal,
        "Defines the capacitive load on the output ports.",
        units="fF",
        deprecated_names=["SYNTH_CAP_LOAD"],
        pdk=True,
    ),
    Variable(
        "MAX_FANOUT_CONSTRAINT",
        int,
        "The max load that the output ports can drive to be used as a constraint on Synthesis and CTS.",
        units="cells",
        deprecated_names=["SYNTH_MAX_FANOUT"],
        pdk=True,
    ),
    Variable(
        "MAX_TRANSITION_CONSTRAINT",
        Optional[Decimal],
        "The max transition time (slew) from high to low or low to high on cell inputs in ns to be used as a constraint on Synthesis and CTS. If not provided, it is calculated at runtime as `10%` of the provided clock period, unless that exceeds the PDK's `DEFAULT_MAX_TRAN` value.",
        units="ns",
        deprecated_names=["SYNTH_MAX_TRAN"],
        pdk=True,
    ),
    Variable(
        "CLOCK_UNCERTAINTY_CONSTRAINT",
        Decimal,
        "Specifies a value for the clock uncertainty/jitter for timing analysis.",
        units="ns",
        deprecated_names=["SYNTH_CLOCK_UNCERTAINTY"],
        pdk=True,
    ),
    Variable(
        "CLOCK_TRANSITION_CONSTRAINT",
        Decimal,
        "Specifies a value for the clock transition/slew for timing analysis.",
        units="ns",
        deprecated_names=["SYNTH_CLOCK_TRANSITION"],
        pdk=True,
    ),
    Variable(
        "TIME_DERATING_CONSTRAINT",
        Decimal,
        "Specifies a derating factor to multiply the path delays with. It specifies the upper and lower ranges of timing.",
        units="%",
        deprecated_names=["SYNTH_TIMING_DERATE"],
        pdk=True,
    ),
    Variable(
        "IO_DELAY_CONSTRAINT",
        Decimal,
        "Specifies the percentage of the clock period used in the input/output delays.",
        units="%",
        deprecated_names=["IO_PCT"],
        pdk=True,
    ),
    # Synthesis
    Variable(
        "SYNTH_DRIVING_CELL",
        str,
        "The cell to drive the input ports, used in synthesis and static timing analysis, in the format `{cell}/{port}`.",
        pdk=True,
    ),
    Variable(
        "SYNTH_CLK_DRIVING_CELL",
        Optional[str],
        "The cell to drive the clock input ports, used in synthesis and static timing analysis, in the format `{cell}/{port}`. If not specified, `SYNTH_DRIVING_CELL` will be used.",
        pdk=True,
    ),
    Variable(
        "SYNTH_TIEHI_CELL",
        str,
        "Defines the tie high cell followed by the port that implements the tie high functionality, in the format `{cell}/{port}`.",
        pdk=True,
    ),
    Variable(
        "SYNTH_TIELO_CELL",
        str,
        "Defines the tie high cell followed by the port that implements the tie low functionality, in the format `{cell}/{port}`.",
        pdk=True,
    ),
    Variable(
        "SYNTH_BUFFER_CELL",
        str,
        "Defines a buffer port to be used by yosys during synthesis: in the format `{cell}/{input_port}/{output_port}`",
        pdk=True,
    ),
    # Clock Tree Synthesis
    Variable(
        "CTS_ROOT_BUFFER",
        str,
        "Defines the cell inserted at the root of the clock tree. Used in CTS.",
        pdk=True,
    ),
    Variable(
        "CTS_CLK_BUFFERS",
        List[str],
        "Defines the list of clock buffers to be used in CTS.",
        deprecated_names=["CTS_CLK_BUFFER_LIST"],
        pdk=True,
    ),
    Variable(
        "CTS_MAX_CAP",
        Decimal,
        "Defines the maximum capacitance, used in CTS.",
        units="pF",
        pdk=True,
    ),
    # Floorplanning
    Variable(
        "FP_WELLTAP_CELL",
        str,
        "Defines the cell used for tap insertion.",
        pdk=True,
    ),
    Variable(
        "FP_ENDCAP_CELL",
        str,
        "Defines so-called 'end-cap' cells- decap cells placed at either sides of a design.",
        pdk=True,
    ),
    Variable(
        "IGNORE_DISCONNECTED_MODULES",
        Optional[List[str]],
        "Modules (or cells) to ignore when checking for disconnected pins.",
        pdk=True,
    ),
    # Placement
    Variable(
        "PLACE_SITE",
        str,
        "Defines the main placement site in placement as specified in the technology LEF files, to generate the placement grid.",
        pdk=True,
    ),
    Variable(
        "PLACE_SITE_WIDTH",
        Decimal,
        "The site width for the previously designated place site.",
        units="µm",
        pdk=True,
    ),
    Variable(
        "PLACE_SITE_HEIGHT",
        Decimal,
        "The site height for the previously designated place site.",
        units="µm",
        pdk=True,
    ),
    Variable(
        "GPL_CELL_PADDING",
        Decimal,
        "Cell padding value (in sites) for global placement. The number will be integer divided by 2 and placed on both sides.",
        units="sites",
        pdk=True,
    ),
    Variable(
        "DPL_CELL_PADDING",
        Decimal,
        "Cell padding value (in sites) for detailed placement. The number will be integer divided by 2 and placed on both sides. Should be <= global placement.",
        units="sites",
        pdk=True,
    ),
    Variable(
        "CELL_PAD_EXCLUDE",
        List[str],
        "Defines a list of cells to be excluded from cell padding.",
        pdk=True,
    ),
    # Antenna
    Variable(
        "DIODE_CELL",
        Optional[str],
        "Defines a diode cell used to fix antenna violations, in the format {name}/{port}.",
        pdk=True,
    ),
    # Routing
    Variable(
        "GRT_LAYER_ADJUSTMENTS",
        List[Decimal],
        "Layer-specific reductions in the routing capacity of the edges between the cells in the global routing graph, delimited by commas. Values range from 0 through 1.",
        pdk=True,
    ),
]
option_variables = [
    # Common
    Variable(
        "DESIGN_DIR",
        Path,
        "The directory of the design. Should be set via command-line arguments or :meth:`Config.load` flags and not actual configuration files. If using a configuration file, ``DESIGN_DIR`` will be the directory where that file exists.",
    ),
    Variable(
        "PDK_ROOT",
        Path,
        "The home path of all PDKs. Should be set via command-line arguments or :meth:`Config.load` flags and not actual configuration files.",
    ),
    Variable(
        "DESIGN_NAME",
        str,
        "The name of the top level module of the design. This is the only variable that MUST be set in every single OpenLane configuration file or dictionary.",
    ),
    Variable(
        "PDK",
        str,
        "Specifies the process design kit (PDK).",
        default="sky130A",
    ),
    Variable(
        "CLOCK_PERIOD",
        Decimal,
        "The clock period for the design.",
        units="ns",
        default=10.0,
    ),
    Variable(
        "CLOCK_PORT",
        Union[None, str, List[str]],
        "The name(s) of the design's clock port(s).",
    ),
    Variable(
        "CLOCK_NET",
        Union[None, str, List[str]],
        "The name of the net input to root clock buffer. If unset, it is presumed to be equal to CLOCK_PORT.",
    ),
    Variable(
        "VDD_NETS",
        Optional[List[str]],
        "Specifies the power nets/pins to be used when creating the power grid for the design.",
    ),
    Variable(
        "GND_NETS",
        Optional[List[str]],
        "Specifies the ground nets/pins to be used when creating the power grid for the design.",
    ),
    Variable(
        "DIE_AREA",
        Optional[str],
        'Specific die area to be used in floorplanning when `FP_SIZING` is set to `absolute`. Specified as a 4-corner rectangle "x0 y0 x1 y1".',
        units="µm",
    ),
    # Macros
    Variable(
        "MACROS",
        Optional[Dict[str, Macro]],
        "A dictionary of Macro definition objects. See {py:class}`openlane.config.Macro` for more info.",
    ),
    Variable(
        "EXTRA_LEFS",
        Optional[List[Path]],
        "Specifies miscellaneous LEF files to be loaded indiscriminately whenever LEFs are loaded.",
    ),
    Variable(
        "EXTRA_VERILOG_MODELS",
        Optional[List[Path]],
        "Specifies miscellaneous Verilog models to be loaded indiscriminately during synthesis.",
        deprecated_names=["VERILOG_FILES_BLACKBOX"],
    ),
    Variable(
        "EXTRA_SPICE_MODELS",
        Optional[List[Path]],
        "Specifies miscellaneous SPICE models to be loaded indiscriminately whenever SPICE models are loaded.",
    ),
    Variable(
        "EXTRA_LIBS",
        Optional[List[Path]],
        "Specifies LIB files of pre-hardened macros used in the current design, used during timing analyses (and during parasitics-based STA as a fallback). These are loaded indiscriminately for all timing corners.",
    ),
    Variable(
        "EXTRA_GDS_FILES",
        Optional[List[Path]],
        "Specifies GDS files of pre-hardened macros used in the current design, used during tape-out.",
    ),
    # Unimplemented - To be moved to steps
    Variable(
        "FP_CONTEXT_DEF",
        Optional[Path],
        "Points to the parent DEF file that includes this macro/design and uses this DEF file to determine the best locations for the pins. It must be used with `FP_CONTEXT_LEF`, otherwise it's considered non-existing. If not set, then the IO pins will be placed based on one of the other methods depending on the rest of the configurations.",
    ),
    Variable(
        "FP_CONTEXT_LEF",
        Optional[Path],
        "Points to the parent LEF file that includes this macro/design and uses this LEF file to determine the best locations for the pins. It must be used with `FP_CONTEXT_DEF`, otherwise it's considered non-existing. If not set, then the IO pins will be placed based on one of the other methods depending on the rest of the configurations.",
    ),
    Variable(
        "FP_PADFRAME_CFG",
        Optional[str],
        "A configuration file passed to `padringer`, a padframe generator.",
    ),
    Variable(
        "GRT_OBS",
        Optional[List[str]],
        'Specifies custom obstruction to be added prior to global routing. List of layer and coordinates: `layer llx lly urx ury`, where `ll` and `ur` stand for "lower left" and "upper right" respectively. (Example: `li1 0 100 1000 300, met5 0 0 1000 500`).',
    ),
    Variable(
        "LVS_INSERT_POWER_PINS",
        bool,
        "Enables power pin insertion before running LVS.",
        default=True,
    ),
    Variable(
        "RUN_CVC",
        bool,
        "Runs the Circuit Validity Checker on the output spice, which is a voltage-aware ERC checker for CDL netlists. Will not run unless supported by the current PDK.",
        default=True,
    ),
    Variable(
        "LEC_ENABLE",
        bool,
        "Enables logic verification using yosys, for comparing each netlist at each stage of the flow with the previous netlist and verifying that they are logically equivalent. Warning: this will increase the runtime significantly.",
        default=False,
    ),
    Variable(
        "CHECK_ASSIGN_STATEMENTS",
        bool,
        "Checks for assign statement in the generated gate level netlist and aborts if any were found.",
        default=False,
    ),
    Variable(
        "FALLBACK_SDC_FILE",
        Path,
        "A fallback SDC file for when a step-specific SDC file is not defined.",
        deprecated_names=["BASE_SDC_FILE", "SDC_FILE"],
        default=Path(os.path.join(get_script_dir(), "base.sdc")),
    ),
]

flow_common_variables = pdk_variables + scl_variables + option_variables
