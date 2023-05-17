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
import re
from decimal import Decimal
from typing import List, Optional, Dict

from .variable import Variable
from .config import Config
from ..state import Path

# Note that values in this file do not take defaults.

pdk_variables = [
    Variable(
        "PDK_ROOT",
        str,
        "The path to all PDKs. This doesn't actually need to be defined by the PDK config file itself.",
    ),
    # Core/Common
    Variable(
        "STD_CELL_LIBRARY",
        str,
        "Specifies the default standard cell library to be used under the specified PDK.",
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
        "A value above which wire lengths generate warnings.",
        units="µm",
    ),
    Variable(
        "TECH_LEFS",
        Dict[str, Path],
        "Map of corner patterns to to technology LEF files. A corner not matched here will not be supported by OpenRCX in the default flow.",
    ),
    Variable(
        "CELL_LEFS",
        List[Path],
        "Path(s) to the cell LEF file(s).",
        deprecated_names=["CELLS_LEF"],
    ),
    Variable(
        "CELL_GDS",
        List[Path],
        "Path(s) to the cell GDSII file(s).",
        deprecated_names=["GDS_FILES", "CELLS_GDS"],
    ),
    Variable(
        "GPIO_PADS_LEF",
        Optional[List[Path]],
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
        Optional[Path],
        "A path to the setup file for Netgen used to configure LVS. If set to None, this PDK will not support Netgen-based steps.",
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
    ## Timing and Power
    Variable(
        "DEFAULT_MAX_TRAN",
        Optional[Decimal],
        "Defines the default maximum transition value used in Synthesis and CTS.\nA minimum of 0.1 * CLOCK_PERIOD and this variable, if defined, is used.",
        units="ns",
    ),
    Variable(
        "WIRE_RC_LAYER",
        Optional[str],
        "A metal layer with which to estimate parasitics in earlier stages of the flow.",
    ),
    Variable(
        "RCX_RULESETS",
        Optional[Dict[str, Path]],
        "Map of corner patterns to OpenRCX extraction rules. A corner not matched by exactly one pattern in this dictionary will not be supported by OpenRCX, and a PDK not specifying this variable will not be supported by OpenRCX.",
    ),
    Variable(
        "DEFAULT_CORNER",
        str,
        "The interconnect/process/voltage/temperature corner (IPVT) to use the characterized lib files compatible with by default.",
    ),
    Variable(
        "STA_CORNERS",
        List[str],
        "A list of fully qualified IPVT (Interconnect, transistor Process, Voltage, and Temperature) timing corners on which to conduct multi-corner static timing analysis.",
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
        units="µm",
    ),
    Variable(
        "FP_PDN_RAIL_OFFSET",
        Decimal,
        "The offset for the power distribution network rails for first metal layer.",
        units="µm",
    ),
    Variable(
        "FP_PDN_VWIDTH",
        Decimal,
        "The strap width for the vertical layer in generated power distribution networks.",
        units="µm",
    ),
    Variable(
        "FP_PDN_VSPACING",
        Decimal,
        "The spacing between vertical straps in generated power distribution networks.",
        units="µm",
    ),
    Variable(
        "FP_PDN_HSPACING",
        Decimal,
        "The spacing between horizontal straps in generated power distribution networks.",
        units="µm",
    ),
    Variable(
        "FP_PDN_HWIDTH",
        Decimal,
        "The strap width for the horizontal layer in generated power distribution networks.",
        units="µm",
    ),
    Variable(
        "FP_PDN_CORE_RING_VWIDTH",
        Decimal,
        "The width for the vertical layer in the core ring of generated power distribution networks.",
        units="µm",
    ),
    Variable(
        "FP_PDN_CORE_RING_HWIDTH",
        Decimal,
        "The width for the horizontal layer in the core ring of generated power distribution networks.",
        units="µm",
    ),
    Variable(
        "FP_PDN_CORE_RING_VSPACING",
        Decimal,
        "The spacing for the vertical layer in the core ring of generated power distribution networks.",
        units="µm",
    ),
    Variable(
        "FP_PDN_CORE_RING_HSPACING",
        Decimal,
        "The spacing for the horizontal layer in the core ring of generated power distribution networks.",
        units="µm",
    ),
    Variable(
        "FP_PDN_CORE_RING_VOFFSET",
        Decimal,
        "The offset for the vertical layer in the core ring of generated power distribution networks.",
        units="µm",
    ),
    Variable(
        "FP_PDN_CORE_RING_HOFFSET",
        Decimal,
        "The offset for the horizontal layer in the core ring of generated power distribution networks.",
        units="µm",
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
    Variable(
        "LIB",
        Dict[str, List[Path]],
        "A map from corner patterns to a list of associated liberty files. Exactly one entry must match the `DEFAULT_CORNER`.",
    ),
    Variable(
        "SYNTH_EXCLUSION_CELL_LIST",
        Path,
        "Path to a text file containing a list of cells to be excluded from the lib file in synthesis alone. If not defined, the original lib file will be used as-is.",
        deprecated_names=["NO_SYNTH_CELL_LIST"],
    ),
    Variable(
        "PNR_EXCLUSION_CELL_LIST",
        Path,
        "Path to a text file containing a list of undesirable or bad (DRC-failed or complex pinout) cells to be excluded from synthesis AND PnR. If not defined, all cells will be used.",
        deprecated_names=["DRC_EXCLUDE_CELL_LIST"],
    ),
    # Synthesis
    Variable(
        "SYNTH_CAP_LOAD",
        Decimal,
        "Defines the capacitive load on the output ports.",
        units="fF",
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
        units="pF",
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
        units="µm",
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
    Variable(
        "IGNORE_DISCONNECTED_MODULES",
        Optional[List[str]],
        "Modules (or cells) to ignore when checking for disconnected pins.",
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
        units="µm",
    ),
    Variable(
        "PLACE_SITE_HEIGHT",
        Decimal,
        "The site height for the previously designated place site.",
        units="µm",
    ),
    Variable(
        "GPL_CELL_PADDING",
        Decimal,
        "Cell padding value (in sites) for global placement. The number will be integer divided by 2 and placed on both sides.",
        units="sites",
    ),
    Variable(
        "DPL_CELL_PADDING",
        Decimal,
        "Cell padding value (in sites) for detailed placement. The number will be integer divided by 2 and placed on both sides. Should be <= global placement.",
        units="sites",
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


def migrate_old_config(config: Config) -> Config:
    new = config.copy()._unlock()
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

    # 5. Interconnect Corners
    del new["RCX_RULES"]
    new["RCX_RULESETS"] = f"nom_* \"{config['RCX_RULES']}\""
    if config.get("RCX_RULES_MIN") is not None:
        del new["RCX_RULES_MIN"]
        new["RCX_RULESETS"] += f" min_* \"{config['RCX_RULES_MIN']}\""
    if config.get("RCX_RULES_MAX") is not None:
        del new["RCX_RULES_MAX"]
        new["RCX_RULESETS"] += f" max_* \"{config['RCX_RULES_MAX']}\""

    del new["TECH_LEF"]
    new["TECH_LEFS"] = f"nom_* \"{config['TECH_LEF']}\""
    if config.get("TECH_LEF_MIN") is not None:
        del new["TECH_LEF_MIN"]
        new["TECH_LEFS"] += f" min_* \"{config['TECH_LEF_MIN']}\""
    if config.get("TECH_LEF_MAX") is not None:
        del new["TECH_LEF_MAX"]
        new["TECH_LEFS"] += f" max_* \"{config['TECH_LEF_MAX']}\""

    # 6. Timing Corners
    lib_sta: Dict[str, List[str]] = {}
    ws = re.compile(r"\s+")

    default_pvt = ""

    def process_sta(key: str):
        nonlocal new, default_pvt
        lib_raw = new.pop(key)
        if lib_raw is None:
            return
        lib = lib_raw.strip()
        lib_list = ws.split(lib)
        first_lib = os.path.basename(lib_list[0])[:-4]
        pvt = first_lib.split("__")[1]
        if default_pvt == "":
            default_pvt = pvt
        corner = f"*_{pvt}"
        lib_sta[corner] = lib_list

    process_sta("LIB_SYNTH")
    process_sta("LIB_SLOWEST")
    process_sta("LIB_FASTEST")

    if new["PDK"].startswith("sky130"):
        new["STA_CORNERS"] = [
            "nom_tt_025C_1v80",
            "nom_ss_100C_1v60",
            "nom_ff_n40C_1v95",
            "min_tt_025C_1v80",
            "min_ss_100C_1v60",
            "min_ff_n40C_1v95",
            "max_tt_025C_1v80",
            "max_ss_100C_1v60",
            "max_ff_n40C_1v95",
        ]
    elif new["PDK"].startswith("gf180mcu"):
        new["STA_CORNERS"] = [
            "nom_tt_025C_5v00",
            "nom_ss_125C_4v50",
            "nom_ff_n40C_5v50",
            "min_tt_025C_5v00",
            "min_ss_125C_4v50",
            "min_ff_n40C_5v50",
            "max_tt_025C_5v00",
            "max_ss_125C_4v50",
            "max_ff_n40C_5v50",
        ]

    new["DEFAULT_CORNER"] = f"nom_{default_pvt}"
    new["LIB"] = lib_sta

    # 7. Disconnected Modules (sky130)
    if new["PDK"].startswith("sky130"):
        new["IGNORE_DISCONNECTED_MODULES"] = "sky130_fd_sc_hd__conb_1"

    # 8. Invalid Variables (gf180mcu)
    if new["PDK"].startswith("gf180mcu"):
        del new["GPIO_PADS_LEF"]
        del new["GPIO_PADS_VERILOG"]

        del new["CARRY_SELECT_ADDER_MAP"]
        del new["FULL_ADDER_MAP"]
        del new["RIPPLE_CARRY_ADDER_MAP"]
        del new["SYNTH_LATCH_MAP"]
        del new["TRISTATE_BUFFER_MAP"]

        del new["KLAYOUT_DRC_TECH_SCRIPT"]

        new[
            "SYNTH_CLK_DRIVING_CELL"
        ] = f"{config['SYNTH_CLK_DRIVING_CELL']}/{config['SYNTH_DRIVING_CELL_PIN']}"
    return new._lock()


all_variables: List[Variable] = pdk_variables + scl_variables
removed_variables: Dict[str, str] = {
    "FAKEDIODE_CELL": "Fake diode-based strategies have been removed.",
    "LIB_SYNTH": "Use the lib dictionary instead.",
}
