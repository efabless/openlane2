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
from decimal import Decimal
from typing import List, Optional, Dict

from .variable import Path, Variable
from .config import Config

pdk_variables = [
    # Core/Common
    Variable(
        "STD_CELL_LIBRARY",
        str,
        "Specifies the standard cell library to be used under the specified PDK.",
    ),
    Variable(
        "STD_CELL_LIBRARY_OPT",
        str,
        "Specifies the standard cell library to be used during resizer optimizations.",
    ),
    Variable(
        "VDD_PIN",
        str,
        "The power pin for the cells.",
    ),
    Variable(
        "GND_PIN",
        str,
        "The ground pin for the cells.",
    ),
    Variable(
        "WIRE_LENGTH_THRESHOLD",
        Optional[Decimal],
        "A value above which wire lengths generate warnings. If `QUIT_ON_LONG_WIRE` is set, the flow will error out instead of simply generating a warning.",
        doc_units="µm",
    ),
    Variable(
        "TECH_LEF",
        Path,
        "Path to the technology LEF file in the nominal extraction corner.",
    ),
    Variable(
        "TECH_LEF_MIN",
        Optional[Path],
        "Path to the technology LEF file in the minimum extraction corner.",
    ),
    Variable(
        "TECH_LEF_MAX",
        Optional[Path],
        "Path to the technology LEF file in the maximum extraction corner.",
    ),
    Variable(
        "CELLS_LEF",
        List[Path],
        "Path(s) to the cell LEF file(s).",
    ),
    Variable(
        "CELLS_GDS",
        List[Path],
        "Path(s) to the cell GDSII file(s).",
        deprecated_names=["GDS_FILES"],
    ),
    Variable(
        "GPIO_PADS_LEF",
        List[Path],
        "Path(s) to GPIO pad LEF file(s).",
    ),
    Variable(
        "GPIO_PADS_LEF_CORE_SIDE",
        Optional[List[Path]],
        "Path(s) to GPIO pad LEF file(s) as used for routing (?).",
    ),
    Variable(
        "GPIO_PADS_VERILOG",
        Optional[List[Path]],
        "Path(s) to GPIO pad Verilog models.",
    ),
    Variable(
        "GPIO_PADS_PREFIX",
        Optional[List[str]],
        "A list of pad cell name prefixes.",
    ),
    # Signoff
    ## Netgen
    Variable(
        "NETGEN_SETUP",
        Path,
        "A path to the setup file for Netgen used to configure LVS.",
        deprecated_names=["NETGEN_SETUP_FILE"],
    ),
    ## Magic
    Variable(
        "MAGICRC",
        Optional[Path],
        "A path to the `.magicrc` file which is sourced before running magic in the flow.",
        deprecated_names=["MAGIC_MAGICRC"],
    ),
    Variable(
        "MAGIC_TECH",
        Optional[Path],
        "A path to a Magic tech file which, mainly, has DRC rules.",
        deprecated_names=["MAGIC_TECH_FILE"],
    ),
    ## Klayout,
    Variable(
        "KLAYOUT_TECH",
        Optional[Path],
        "A path to the KLayout layer technology (.lyt) file.",
    ),
    Variable(
        "KLAYOUT_PROPERTIES",
        Optional[Path],
        "A path to the KLayout layer properties (.lyp) file.",
    ),
    Variable(
        "KLAYOUT_DRC_TECH_SCRIPT",
        Optional[Path],
        "A path to a KLayout DRC tech script.",
    ),
    Variable(
        "KLAYOUT_DEF_LAYER_MAP",
        Optional[Path],
        "A path to the KLayout LEF/DEF layer mapping (.map) file.",
    ),
    Variable(
        "KLAYOUT_XOR_IGNORE_LAYERS",
        Optional[List[str]],
        "KLayout layers to ignore during XOR operations.",
    ),
    # Timing and Power
    Variable(
        "DEFAULT_MAX_TRAN",
        Optional[Decimal],
        "Defines the default maximum transition value used in Synthesis and CTS.\nA minimum of 0.1 * CLOCK_PERIOD and this variable, if defined, is used.",
        doc_units="ns",
    ),
    Variable(
        "WIRE_RC_LAYER",
        Optional[str],
        "A metal layer with which to estimate parasitics in earlier stages of the flow.",
    ),
    Variable(
        "RCX_RULES",
        Path,
        "Path to the OpenRCX extraction rules for the nominal process corner.",
    ),
    Variable(
        "RCX_RULES_MIN",
        Optional[Path],
        "Path to the OpenRCX extraction rules for the minimum process corner.",
    ),
    Variable(
        "RCX_RULES_MAX",
        Optional[Path],
        "Path to the OpenRCX extraction rules for the maximum process corner.",
    ),
    # Floorplanning
    Variable(
        "FP_TRACKS_INFO",
        Path,
        "A path to the a classic OpenROAD `.tracks` file. Used by the floorplanner to generate tracks.",
        deprecated_names=["TRACKS_INFO_FILE"],
    ),
    Variable(
        "FP_TAPCELL_DIST",
        Decimal,
        "The distance between tap cell columns.",
        doc_units="µm",
    ),
    Variable(
        "FP_PDN_RAIL_OFFSET",
        Decimal,
        "The offset for the power distribution network rails for first metal layer.",
        doc_units="µm",
    ),
    Variable(
        "FP_PDN_VWIDTH",
        Decimal,
        "The strap width for the vertical layer in generated power distribution networks.",
        doc_units="µm",
    ),
    Variable(
        "FP_PDN_VSPACING",
        Decimal,
        "The spacing between vertical straps in generated power distribution networks.",
        doc_units="µm",
    ),
    Variable(
        "FP_PDN_HSPACING",
        Decimal,
        "The spacing between horizontal straps in generated power distribution networks.",
        doc_units="µm",
    ),
    Variable(
        "FP_PDN_HWIDTH",
        Decimal,
        "The strap width for the horizontal layer in generated power distribution networks.",
        doc_units="µm",
    ),
    Variable(
        "FP_PDN_CORE_RING_VWIDTH",
        Decimal,
        "The width for the vertical layer in the core ring of generated power distribution networks.",
        doc_units="µm",
    ),
    Variable(
        "FP_PDN_CORE_RING_HWIDTH",
        Decimal,
        "The width for the horizontal layer in the core ring of generated power distribution networks.",
        doc_units="µm",
    ),
    Variable(
        "FP_PDN_CORE_RING_VSPACING",
        Decimal,
        "The spacing for the vertical layer in the core ring of generated power distribution networks.",
        doc_units="µm",
    ),
    Variable(
        "FP_PDN_CORE_RING_HSPACING",
        Decimal,
        "The spacing for the horizontal layer in the core ring of generated power distribution networks.",
        doc_units="µm",
    ),
    Variable(
        "FP_PDN_CORE_RING_VOFFSET",
        Decimal,
        "The offset for the vertical layer in the core ring of generated power distribution networks.",
        doc_units="µm",
    ),
    Variable(
        "FP_PDN_CORE_RING_HOFFSET",
        Decimal,
        "The offset for the horizontal layer in the core ring of generated power distribution networks.",
        doc_units="µm",
    ),
    Variable(
        "FP_IO_HLAYER",
        str,
        "The metal layer on which to place horizontal IO pins, i.e., the top and bottom of the die.",
    ),
    Variable(
        "FP_IO_VLAYER",
        str,
        "The metal layer on which to place vertial IO pins, i.e., the top and bottom of the die.",
    ),
    Variable("RT_MIN_LAYER", str, "The lowest metal layer to route on."),
    Variable("RT_MAX_LAYER", str, "The highest metal layer to route on."),
]

scl_variables = [
    # Common
    Variable(
        "SCL_GROUND_PINS",
        List[str],
        "SCL-specific ground pins",
        deprecated_names=["STD_CELL_GROUND_PINS"],
    ),
    Variable(
        "SCL_POWER_PINS",
        List[str],
        "SCL-specific power pins",
        deprecated_names=["STD_CELL_POWER_PINS"],
    ),
    Variable(
        "FILL_CELL",
        List[str],
        "A list of cell names or wildcards of fill cells to be used in fill insertion.",
    ),
    Variable(
        "DECAP_CELL",
        List[str],
        "A list of cell names or wildcards of decap cells to be used in fill insertion.",
    ),
    # Synthesis
    Variable(
        "LIB",
        List[Path],
        "Path to the lib file to be used during synthesis.",
        deprecated_names=["LIB_SYNTH"],
    ),
    Variable(
        "NO_SYNTH_CELL_LIST",
        Path,
        "Path to a text file containing a list of cells to be excluded from the liberty file in synthesis alone. If not defined, the original liberty file will be used as-is.",
    ),
    Variable(
        "BAD_CELL_LIST",
        Path,
        "Path to a text file containing a list of bad (DRC-failed or complex pinout) cells to be excluded from synthesis AND timing optimizations. If not defined, all cells will be used.",
        deprecated_names=["DRC_EXCLUDE_CELL_LIST"],
    ),
    # Static Timing Analysis
    Variable(
        "LIB_TYPICAL",
        List[Path],
        "Path to the lib file to be used during typical timing corner static timing analysis.",
        deprecated_names=["LIB_SYNTH_TYPICAL"],
    ),
    Variable(
        "LIB_SLOWEST",
        List[Path],
        "Path to the lib file to be used during slowest timing corner static timing analysis.",
        deprecated_names=["LIB_SYNTH_SLOWEST"],
    ),
    Variable(
        "LIB_FASTEST",
        List[Path],
        "Path to the lib file to be used during fastest timing corner static timing analysis.",
        deprecated_names=["LIB_SYNTH_FASTEST"],
    ),
    # Synthesis
    Variable(
        "SYNTH_CAP_LOAD",
        Decimal,
        "Defines the capacitive load on the output ports.",
        doc_units="fF",
    ),
    Variable(
        "SYNTH_DRIVING_CELL",
        str,
        "The cell to drive the input ports, used in synthesis and static timing analysis, in the format `{cell}/{port}`.",
    ),
    Variable(
        "SYNTH_CLK_DRIVING_CELL",
        Optional[str],
        "The cell to drive the clock input ports, used in synthesis and static timing analysis, in the format `{cell}/{port}`. If not specified, `SYNTH_DRIVING_CELL` will be used.",
    ),
    Variable(
        "SYNTH_TIEHI_CELL",
        str,
        "Defines the tie high cell followed by the port that implements the tie high functionality, in the format `{cell}/{port}`.",
    ),
    Variable(
        "SYNTH_TIELO_CELL",
        str,
        "Defines the tie high cell followed by the port that implements the tie low functionality, in the format `{cell}/{port}`.",
    ),
    Variable(
        "SYNTH_BUFFER_CELL",
        str,
        "Defines a buffer port to be used by yosys during synthesis: in the format `{cell}/{input_port}/{output_port}`",
    ),
    ## Mappings
    Variable(
        "SYNTH_LATCH_MAP",
        Optional[Path],
        "A path to a file contianing the latch mapping for Yosys.",
    ),
    Variable(
        "SYNTH_TRISTATE_MAP",
        Optional[Path],
        "A path to a file contianing the tri-state buffer mapping for Yosys.",
        deprecated_names=["TRISTATE_BUFFER_MAP"],
    ),
    Variable(
        "SYNTH_CSA_MAP",
        Optional[Path],
        "A path to a file containing the carry-select adder mapping for Yosys.",
        deprecated_names=["CARRY_SELECT_ADDER_MAP"],
    ),
    Variable(
        "SYNTH_RCA_MAP",
        Optional[Path],
        "A path to a file containing the ripple-carry adder mapping for Yosys.",
        deprecated_names=["RIPPLE_CARRY_ADDER_MAP"],
    ),
    Variable(
        "SYNTH_FA_MAP",
        Optional[Path],
        "A path to a file containing the full adder mapping for Yosys.",
        deprecated_names=["FULL_ADDER_MAP"],
    ),
    Variable(
        "SYNTH_MUX_MAP",
        Optional[Path],
        "A path to a file containing the mux mapping for Yosys.",
    ),
    Variable(
        "SYNTH_MUX4_MAP",
        Optional[Path],
        "A path to a file containing the mux4 mapping for Yosys.",
    ),
    # Clock Tree Synthesis
    Variable(
        "CELL_CLK_PORT",
        str,
        "Name of the clock port used in all cells.",
    ),
    Variable(
        "CTS_ROOT_BUFFER",
        str,
        "Defines the cell inserted at the root of the clock tree. Used in CTS.",
    ),
    Variable(
        "CTS_CLK_BUFFERS",
        List[str],
        "Defines the list of clock buffers to be used in CTS.",
        deprecated_names=["CTS_CLK_BUFFER_LIST"],
    ),
    Variable(
        "CTS_MAX_CAP",
        Decimal,
        "Defines the maximum capacitance, used in CTS.",
        doc_units="pF",
    ),
    # Floorplanning
    Variable(
        "FP_WELLTAP_CELL",
        str,
        "Defines the cell used for tap insertion.",
    ),
    Variable(
        "FP_ENDCAP_CELL",
        str,
        "Defines so-called 'end-cap' cells- decap cells placed at either sides of a design.",
    ),
    Variable(
        "FP_PDN_RAILS_LAYER",
        str,
        "Defines the metal layer used for PDN rails.",
    ),
    Variable(
        "FP_PDN_RAIL_WIDTH",
        Decimal,
        "Defines the width of PDN rails on the `FP_PDN_RAILS_LAYER` layer.",
        doc_units="µm",
    ),
    Variable(
        "FP_PDN_UPPER_LAYER",
        str,
        "Defines the upper PDN layer.",
    ),
    Variable(
        "FP_PDN_LOWER_LAYER",
        str,
        "Defines the lower PDN layer.",
    ),
    # Placement
    Variable(
        "PLACE_SITE",
        str,
        "Defines the main placement site in placement as specified in the technology LEF files, to generate the placement grid.",
    ),
    Variable(
        "PLACE_SITE_WIDTH",
        Decimal,
        "The site width for the previously designated place site.",
        doc_units="µm",
    ),
    Variable(
        "PLACE_SITE_HEIGHT",
        Decimal,
        "The site height for the previously designated place site.",
        doc_units="µm",
    ),
    Variable(
        "GPL_CELL_PADDING",
        Optional[Decimal],
        "Cell padding value (in sites) for global placement. Using this is not recommended as you can simply use the density control for global placement.",
        doc_units="sites",
    ),
    Variable(
        "DPL_CELL_PADDING",
        Decimal,
        "Defines the number of sites to pad the cells lef views with during detailed placement. The number will be integer divided by 2 and placed on both sides.",
        doc_units="sites",
    ),
    Variable(
        "CELL_PAD_EXCLUDE",
        List[str],
        "Defines a list of cells to be excluded from cell padding.",
    ),
    # Antenna
    Variable(
        "DIODE_CELL",
        Optional[str],
        "Defines a diode cell used to fix antenna violations, in the format {name}/{port}.",
    ),
    Variable(
        "FAKEDIODE_CELL",
        Optional[str],
        "Defines a diode cell used to fix antenna violations. Name only.",
    ),
    # Routing
    Variable(
        "GRT_LAYER_ADJUSTMENTS",
        List[Decimal],
        "Layer-specific reductions in the routing capacity of the edges between the cells in the global routing graph, delimited by commas. Values range from 0 through 1.",
    ),
    # CVC
    Variable(
        "CVC_SCRIPTS_DIR",
        Optional[Path],
        "Path to a directory of Circuit Validity Checker (CVC) scripts for the relevant PDK. Must contain the following set of files: `cvcrc`, an initialization file, `cdl.awk`, an awk script to remove black box definitions from SPICE files, `models`, cell models, and finally `power.awk`, an awk script that adds power information to the verilog netlists.\nIf this path is not defined, this PDK will be marked incompatible with CVC.",
    ),
]

PDKVariablesByID: Dict[str, Variable] = {
    variable.name: variable for variable in pdk_variables
}


def migrate_old_config(config: Config) -> Config:
    new = config.copy()
    # 1. Migrate SYNTH_DRIVING_CELL
    del new["SYNTH_DRIVING_CELL"]
    del new["SYNTH_DRIVING_CELL_PIN"]
    new[
        "SYNTH_DRIVING_CELL"
    ] = f"{config['SYNTH_DRIVING_CELL']}/{config['SYNTH_DRIVING_CELL_PIN']}"

    # 2. Migrate SYNTH_TIE{HI,LO}_CELL
    del new["SYNTH_TIEHI_PORT"]
    new["SYNTH_TIEHI_CELL"] = "/".join(config["SYNTH_TIEHI_PORT"].split(" "))

    del new["SYNTH_TIELO_PORT"]
    new["SYNTH_TIELO_CELL"] = "/".join(config["SYNTH_TIELO_PORT"].split(" "))

    # 3. Migrate SYNTH_BUFFER_CELL
    del new["SYNTH_MIN_BUF_PORT"]
    new["SYNTH_BUFFER_CELL"] = "/".join(config["SYNTH_MIN_BUF_PORT"].split(" "))

    # 4. Migrate DIODE_CELL
    del new["DIODE_CELL"]
    del new["DIODE_CELL_PIN"]
    new["DIODE_CELL"] = f"{config['DIODE_CELL']}/{config['DIODE_CELL_PIN']}"

    return new


pdk_removed_variables: Dict[str, str] = {}


def validate_pdk_config(
    config: Config,
    ignore_keys: List[str],
    processed_so_far: Optional[Config] = None,
):
    migrated = migrate_old_config(config)
    return Variable.validate_config(
        migrated,
        ignore_keys,
        pdk_variables + scl_variables,
        removed=pdk_removed_variables,
        processed_so_far=processed_so_far,
    )
