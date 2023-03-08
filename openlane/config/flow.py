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

from .variable import Path, Variable, StringEnum

all_variables = [
    # Common
    Variable(
        "DESIGN_NAME",
        str,
        "The name of the top level module of the design. This is the only required variable for all steps and all flows.",
    ),
    Variable(
        "PDK",
        str,
        "Specifies the process design kit (PDK).",
        default="sky130A",
    ),
    Variable(
        "PRIMARY_SIGNOFF_TOOL",
        StringEnum("PRIMARY_SIGNOFF_TOOL", ["magic", "klayout"]),
        "Specify the primary signoff tool for taping out.",
        default="magic",
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
        Optional[str],
        "The name of the design's clock port.",
    ),
    Variable(
        "CLOCK_NET",
        Optional[str],
        "The name of the net input to root clock buffer.",
        default="ref::$CLOCK_PORT",
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
        units="μm",
    ),
    # Macros
    Variable(
        "EXTRA_VERILOG_MODELS",
        Optional[List[Path]],
        "Black-boxed Verilog models of pre-hardened macros used in the current design, used in synthesis.",
        deprecated_names=["VERILOG_FILES_BLACKBOX"],
    ),
    Variable(
        "EXTRA_SPICE_MODELS",
        Optional[List[Path]],
        "Black-boxed SPICE models of pre-hardened macros used in the current design, used in LVS.",
    ),
    Variable(
        "EXTRA_LEFS",
        Optional[List[Path]],
        "Specifies LEF files of pre-hardened macros used in the current design, used in placement and routing.",
    ),
    Variable(
        "EXTRA_LIBS",
        Optional[List[Path]],
        "Specifies LIB files of pre-hardened macros used in the current design, used during timing analysis. (Optional).",
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
        "SYNTH_USE_PG_PINS_DEFINES",
        Optional[List[str]],
        "Specifies the power guard used in the verilog source code to specify the power and ground pins. This is used to automatically extract `VDD_NETS` and `GND_NET` variables from the verilog, with the assumption that they will be order `inout vdd1, inout gnd1, inout vdd2, inout gnd2, ...`.",
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
        "RUN_KLAYOUT_DRC",
        bool,
        "Enables running KLayout DRC on GDSII produced by magic.",
        default=False,
    ),
    Variable(
        "RUN_CVC",
        bool,
        "Runs the Circuit Validity Checker on the output spice, which is a voltage-aware ERC checker for CDL netlists. Will not run unless supported by the current PDK.",
        default=True,
    ),
    Variable(
        "KLAYOUT_DRC_KLAYOUT_GDS",
        bool,
        "Enables running KLayout DRC on GDSII produced by KLayout.",
        default=False,
    ),
    Variable(
        "LEC_ENABLE",
        bool,
        "Enables logic verification using yosys, for comparing each netlist at each stage of the flow with the previous netlist and verifying that they are logically equivalent. Warning: this will increase the runtime significantly.",
        default=False,
    ),
    Variable(
        "CHECK_UNMAPPED_CELLS",
        bool,
        "Checks if there are unmapped cells after synthesis and aborts if any was found.",
        default=True,
    ),
    Variable(
        "CHECK_ASSIGN_STATEMENTS",
        bool,
        "Checks for assign statement in the generated gate level netlist and aborts if any were found.",
        default=False,
    ),
]
removed_variables: Dict[str, str] = {
    "PL_RANDOM_GLB_PLACEMENT": "The random global placer no longer yields a tangible benefit with newer versions of OpenROAD.",
    "PL_RANDOM_INITIAL_PLACEMENT": "A random initial placer no longer yields a tangible benefit with newer versions of OpenROAD.",
    "KLAYOUT_XOR_GDS": "The GDS output is of limited utility compared to the XML database.",
    "KLAYOUT_XOR_XML": "The XML database is always generated.",
    "MAGIC_GENERATE_GDS": "The GDS view is always generated when MAGIC_RUN_STREAMOUT is set.",
    "CLOCK_BUFFER_FANOUT": "The simple CTS script that used this variable no longer exists.",
    "FP_IO_HMETAL": "Replaced by FP_IO_HLAYER in the PDK configuration variables, which uses a more specific layer name.",
    "FP_IO_VMETAL": "Replaced by FP_IO_VLAYER in the PDK  configuration variables, which uses a more specific layer name.",
    "GLB_OPTIMIZE_MIRRORING": "Shares DPL_OPTIMIZE_MIRRORING.",
    "GRT_MAX_DIODE_INS_ITERS": "Relevant diode insertion strategies removed.",
    "TAKE_LAYOUT_SCROT": "Buggy/dubious utility.",
    "GENERATE_FINAL_SUMMARY_REPORT": "To be specified via API/CLI- not much of a configuration variable.",
    "USE_GPIO_PADS": "Add the pad's files to EXTRA_LEFS and EXTRA_VERILOG_MODELS as apprioriate.",
}
