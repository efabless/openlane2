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
from enum import Enum
from typing import Dict


class DesignFormat(Enum):
    """
    A list of design formats that may be kept in the state object.

    The value of the enum is a tuple with the following entries:
        - [0] id
        - [1] file extension
        - [2] human readable name
    """

    NETLIST = (
        "nl",
        "nl.v",
        "Verilog Netlist",
    )
    POWERED_NETLIST = (
        "pnl",
        "pnl.v",
        "Powered Verilog Netlist",
    )

    DEF = (
        "def",
        "def",
        "Design Exchange Format",
    )
    LEF = (
        "lef",
        "lef",
        "Library Exchange Format",
    )
    ODB = (
        "odb",
        "odb",
        "OpenDB Database",
    )

    SDC = (
        "sdc",
        "sdc",
        "Design Constraints",
    )
    SDF = (
        "sdf",
        "sdf",
        "Standard Delay Format",
    )
    SPEF = (
        "spef",
        "spef",
        "Standard Parasitics Extraction Format",
    )
    LIB = (
        "lib",
        "lib",
        "Lib",
    )
    SPICE = (
        "spice",
        "spice",
        "Simulation Program with Integrated Circuit Emphasis",
    )

    GDS = (
        "gds",
        "gds",
        "GDSII Stream",
    )
    MAG_GDS = (
        "mag_gds",
        "magic.gds",
        "GDSII Stream (Magic)",
    )
    KLAYOUT_GDS = (
        "klayout_gds",
        "klayout.gds",
        "GDSII Stream (KLayout)",
    )


DesignFormatByID: Dict[str, DesignFormat] = {
    format.value[0]: format for format in DesignFormat
}
