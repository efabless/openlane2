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
    )
    SPEF: DesignFormatObject = DesignFormatObject(
        "spef",
        "nom.spef",
        "Standard Parasitics Extraction Format (Nominal Corner)",
    )
    SPEF_MIN: DesignFormatObject = DesignFormatObject(
        "spef_min",
        "min.spef",
        "Standard Parasitics Extraction Format (Minimum Corner)",
        "spef",
    )
    SPEF_MAX: DesignFormatObject = DesignFormatObject(
        "spef_max",
        "max.spef",
        "Standard Parasitics Extraction Format (Maximum Corner)",
        "spef",
    )
    LIB: DesignFormatObject = DesignFormatObject(
        "lib",
        "lib",
        "LIB Timing Library Format",
    )
    SPICE: DesignFormatObject = DesignFormatObject(
        "spice",
        "spice",
        "Simulation Program with Integrated Circuit Emphasis",
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

    @staticmethod
    def by_id(id: str) -> Optional["DesignFormat"]:
        return _designformat_by_id.get(id)


_designformat_by_id: Dict[str, "DesignFormat"] = {
    format.value.id: format for format in DesignFormat
}
