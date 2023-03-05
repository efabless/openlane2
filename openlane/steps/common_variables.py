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
from typing import Optional, List

from ..config import Variable

io_layer_variables = [
    Variable(
        "FP_IO_VEXTEND",
        Decimal,
        "Extends the vertical io pins outside of the die by the specified units.",
        default=0,
        units="μm",
    ),
    Variable(
        "FP_IO_HEXTEND",
        Decimal,
        "Extends the horizontal io pins outside of the die by the specified units.",
        default=0,
        units="μm",
    ),
    Variable(
        "FP_IO_VLENGTH",
        Decimal,
        "The length of the vertical IOs.",
        default=4,
        units="µm",
    ),
    Variable(
        "FP_IO_HLENGTH",
        Decimal,
        "The length of the horizontal IOs.",
        default=4,
        units="µm",
    ),
    Variable(
        "FP_IO_VTHICKNESS_MULT",
        Decimal,
        "A multiplier for vertical pin thickness. Base thickness is the pins layer minwidth.",
        default=2,
    ),
    Variable(
        "FP_IO_HTHICKNESS_MULT",
        Decimal,
        "A multiplier for horizontal pin thickness. Base thickness is the pins layer minwidth.",
        default=2,
    ),
]

pdn_variables = [
    Variable(
        "FP_PDN_VOFFSET",
        Decimal,
        "The offset of the vertical power stripes on the metal layer 4 in the power distribution network.",
        default=16.32,
        units="μm",
    ),
    Variable(
        "FP_PDN_VPITCH",
        Decimal,
        "The pitch of the vertical power stripes on the metal layer 4 in the power distribution network.",
        default=153.6,
        units="μm",
    ),
    Variable(
        "FP_PDN_HOFFSET",
        Decimal,
        "The offset of the horizontal power stripes on the metal layer 5 in the power distribution network.",
        default=16.65,
        units="μm",
    ),
    Variable(
        "FP_PDN_HPITCH",
        Decimal,
        "The pitch of the horizontal power stripes on the metal layer 5 in the power distribution network.",
        default=153.18,
        units="μm",
    ),
    Variable(
        "FP_PDN_AUTO_ADJUST",
        bool,
        "Decides whether or not the flow should attempt to re-adjust the power grid, in order for it to fit inside the core area of the design, if needed.",
        default=True,
    ),
    Variable(
        "FP_PDN_SKIPTRIM",
        bool,
        "Enables `-skip_trim` option during pdngen which skips the metal trim step, which attempts to remove metal stubs.",
        default=True,
    ),
    Variable(
        "FP_PDN_CORE_RING",
        bool,
        "Enables adding a core ring around the design. More details on the control variables in the PDK config documentation.",
        default=False,
    ),
    Variable(
        "FP_PDN_ENABLE_RAILS",
        bool,
        "Enables the creation of rails in the power grid.",
        default=True,
    ),
    Variable(
        "FP_PDN_CHECK_NODES",
        bool,
        "Enables checking for unconnected nodes in the power grid.",
        default=True,
    ),
    Variable(
        "FP_PDN_HORIZONTAL_HALO",
        str,
        "Sets the horizontal halo around the macros during power grid insertion.",
        default=10,
        units="µm",
    ),
    Variable(
        "FP_PDN_VERTICAL_HALO",
        Decimal,
        "Sets the vertical halo around the macros during power grid insertion.",
        default="expr::$FP_PDN_HORIZONTAL_HALO",
        units="µm",
    ),
    Variable(
        "DESIGN_IS_CORE",
        bool,
        "Controls the layers used in the power grid. Depending on whether the design is the core of a chip or a macro inside the core.",
        default=True,
    ),
]

routing_layer_variables = [
    Variable(
        "RT_CLOCK_MIN_LAYER",
        Optional[str],
        "The name of lowest layer to be used in routing the clock net.",
    ),
    Variable(
        "RT_CLOCK_MAX_LAYER",
        Optional[str],
        "The name of highest layer to be used in routing the clock net.",
    ),
    Variable(
        "GRT_ADJUSTMENT",
        Decimal,
        "Reduction in the routing capacity of the edges between the cells in the global routing graph for all layers. Values range from 0 to 1.  1 = most reduction, 0 = least reduction.",
        default=0.3,
    ),
    Variable(
        "GRT_MACRO_EXTENSION",
        int,
        "Sets the number of GCells added to the blockages boundaries from macros. A GCell is typically defined in terms of Mx routing tracks. The default GCell size is 15 M3 pitches.",
        default=0,
    ),
]


dpl_variables = [
    Variable(
        "PL_OPTIMIZE_MIRRORING",
        bool,
        "Specifies whether or not to run an optimize_mirroring pass whenever detailed placement happens. This pass will mirror the cells whenever possible to optimize the design.",
        default=True,
    ),
    Variable(
        "PL_MAX_DISPLACEMENT_X",
        Decimal,
        "Specifies how far an instance can be moved along the X-axis when finding a site where it can be placed during detailed placement.",
        default=500,
        units="μm",
    ),
    Variable(
        "PL_MAX_DISPLACEMENT_Y",
        Decimal,
        "Specifies how far an instance can be moved along the Y-axis when finding a site where it can be placed during detailed placement.",
        default=100,
        units="μm",
    ),
]


rsz_variables = dpl_variables + [
    Variable(
        "RSZ_DONT_TOUCH_RX",
        str,
        'A single regular expression designating nets as "don\'t touch" by resizer optimizations.',
        default="$^",
        deprecated_names=["UNBUFFER_NETS"],
    ),
    Variable(
        "RSZ_DONT_USE_CELLS",
        Optional[List[str]],
        "An optional list of cells to not use during resizer optimizations.",
        deprecated_names=["DONT_USE_CELLS"],
    ),
]

constraint_variables = [
    Variable(
        "MAX_FANOUT_CONSTRAINT",
        int,
        "The max load that the output ports can drive to be used as a constraint on Synthesis and CTS.",
        default=10,
        units="cells",
        deprecated_names=["SYNTH_MAX_FANOUT"],
    ),
    Variable(
        "MAX_TRANSITION_CONSTRAINT",
        Optional[Decimal],
        "The max transition time (slew) from high to low or low to high on cell inputs in ns to be used as a constraint on Synthesis and CTS. If not provided, it is calculated at runtime as `10%` of the provided clock period, unless that exceeds the PDK's `DEFAULT_MAX_TRAN` value.",
        units="ns",
        deprecated_names=["SYNTH_MAX_TRAN"],
    ),
    Variable(
        "CLOCK_UNCERTAINTY_CONSTRAINT",
        Decimal,
        "Specifies a value for the clock uncertainty/jitter for timing analysis.",
        default=0.25,
        units="ns",
        deprecated_names=["SYNTH_CLOCK_UNCERTAINTY"],
    ),
    Variable(
        "CLOCK_TRANSITION_CONSTRAINT",
        Decimal,
        "Specifies a value for the clock transition/slew for timing analysis.",
        default=0.15,
        units="ns",
        deprecated_names=["SYNTH_CLOCK_TRANSITION"],
    ),
    Variable(
        "TIME_DERATING_CONSTRAINT",
        Decimal,
        "Specifies a derating factor to multiply the path delays with. It specifies the upper and lower ranges of timing.",
        default=5,
        units="%",
        deprecated_names=["SYNTH_TIMING_DERATE"],
    ),
    Variable(
        "IO_DELAY_CONSTRAINT",
        Decimal,
        "Specifies the percentage of the clock period used in the input/output delays.",
        default=20,
        units="%",
        deprecated_names=["IO_PCT"],
    ),
]
