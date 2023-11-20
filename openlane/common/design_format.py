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
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class DesignFormatObject:
    id: str
    extension: str
    name: str
    folder_override: Optional[str] = None
    multiple: bool = False

    @property
    def folder(self) -> str:
        return self.folder_override or self.id


class DesignFormat(Enum):
    """
    A list of design formats that may be kept in the state object.
    """

    NETLIST: DesignFormatObject = DesignFormatObject(
        "nl",
        "nl.v",
        "Verilog Netlist",
    )
    POWERED_NETLIST: DesignFormatObject = DesignFormatObject(
        "pnl",
        "pnl.v",
        "Powered Verilog Netlist",
    )
    POWERED_NETLIST_SIMULATION: DesignFormatObject = DesignFormatObject(
        "pnl-simulation",
        "pnl-sim.v",
        "Powered Verilog Netlist For Simulation (Without Fill Cells)",
        folder_override="pnl",
    )
    POWERED_NETLIST_NO_PHYSICAL_CELLS: DesignFormatObject = DesignFormatObject(
        "pnl-npc",
        "pnl-npc.v",
        "Powered Verilog Netlist Without Physical Cells (Fill Cells and Diode Cells)",
        folder_override="pnl",
    )

    DEF: DesignFormatObject = DesignFormatObject(
        "def",
        "def",
        "Design Exchange Format",
    )
    LEF: DesignFormatObject = DesignFormatObject(
        "lef",
        "lef",
        "Library Exchange Format",
    )
    OPENROAD_LEF: DesignFormatObject = DesignFormatObject(
        "openroad-lef",
        "openroad.lef",
        "Library Exchange Format Generated by OpenROAD",
        folder_override="lef",
    )
    ODB: DesignFormatObject = DesignFormatObject(
        "odb",
        "odb",
        "OpenDB Database",
    )

    SDC: DesignFormatObject = DesignFormatObject(
        "sdc",
        "sdc",
        "Design Constraints",
    )
    SDF: DesignFormatObject = DesignFormatObject(
        "sdf",
        "sdf",
        "Standard Delay Format",
        multiple=True,
    )
    SPEF: DesignFormatObject = DesignFormatObject(
        "spef",
        "spef",
        "Standard Parasitics Extraction Format",
        multiple=True,  # nom, min, max, ...
    )
    LIB: DesignFormatObject = DesignFormatObject(
        "lib",
        "lib",
        "LIB Timing Library Format",
        multiple=True,
    )
    SPICE: DesignFormatObject = DesignFormatObject(
        "spice",
        "spice",
        "Simulation Program with Integrated Circuit Emphasis",
    )

    MAG: DesignFormatObject = DesignFormatObject(
        "mag",
        "mag",
        "Magic VLSI View",
    )

    GDS: DesignFormatObject = DesignFormatObject(
        "gds",
        "gds",
        "GDSII Stream",
    )
    MAG_GDS: DesignFormatObject = DesignFormatObject(
        "mag_gds",
        "magic.gds",
        "GDSII Stream (Magic)",
    )
    KLAYOUT_GDS: DesignFormatObject = DesignFormatObject(
        "klayout_gds",
        "klayout.gds",
        "GDSII Stream (KLayout)",
    )

    JSON_HEADER: DesignFormatObject = DesignFormatObject(
        "json_h",
        "h.json",
        "Design JSON Header File",
    )

    def __str__(self) -> str:
        return self.value.id

    @staticmethod
    def by_id(id: str) -> Optional["DesignFormat"]:
        return _designformat_by_id.get(id)


_designformat_by_id: Dict[str, "DesignFormat"] = {
    format.value.id: format for format in DesignFormat
}
