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
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, ClassVar
from deprecated.sphinx import deprecated


class DFMetaclass(type):
    def __getattr__(Self, key: str):
        if df := Self.factory.get(key):
            return df
        raise AttributeError(
            "Unknown DesignFormat or Type[DesignFormat] attribute",
            key,
            Self,
        )


@dataclass
class DesignFormat(metaclass=DFMetaclass):
    """
    Metadata about the various possible text or binary representations (views)
    of any design.

    For example, ``DesignFormat.NETLIST.value`` has the metadata for Netlist
    views.

    :param id: A lowercase alphanumeric identifier for the design format.
        Some IDs in OpenLane 2.X use dashes. This is an inconsistency that will
        be addressed in the next major version of OpenLane as it would be a
        breaking change.
    :param extension: The file extension for designs saved in this format.
    :param name: A human-readable name for this design format.
    :param folder_override: The subdirectory when
        :meth:`openlane.state.State.save_snapshot` is called on a state. If
        unset, the value for ``id`` will be used.
    :param multiple: Whether this view may have multiple files (typically, files
        that are different across multiple corners or similar.)
    """

    id: str
    extension: str
    full_name: str
    name: str
    alts: List[str] = field(default_factory=list)
    folder_override: Optional[str] = None
    multiple: bool = False

    @property
    def folder(self) -> str:
        return self.folder_override or self.id

    @property
    @deprecated(
        "The DesignFormat is directly returned now, no need for .value",
        version="3.0.0",
        action="once",
    )
    def value(self) -> DesignFormat:
        return self

    def register(self):
        self.__class__.factory.register(self)

    def __str__(self) -> str:
        return self.id

    def __hash__(self):
        return hash(self.id)

    @staticmethod
    @deprecated(
        "Use DesignFormat.factory.get",
        version="3.0.0",
        action="once",
    )
    def by_id(id: str) -> Optional["DesignFormat"]:
        return DesignFormat.factory.get(id)

    class DesignFormatFactory(object):
        """
        A factory singleton for DesignFormats, allowing them to be registered
        and then retrieved by a string name.

        See https://en.wikipedia.org/wiki/Factory_(object-oriented_programming) for
        a primer.
        """

        _registry: ClassVar[Dict[str, DesignFormat]] = {}

        @classmethod
        def register(Self, df: DesignFormat) -> DesignFormat:
            """
            Adds a DesignFormat to the registry using its
            :attr:`DesignFormat.id`, :attr:`DesignFormat.name` and
            :attr:`DesignFormat.alts` attributes.
            """
            Self._registry[df.id] = df
            Self._registry[df.name] = df
            for alt in df.alts:
                Self._registry[alt] = df
            return df

        @classmethod
        def get(Self, name: str) -> Optional[DesignFormat]:
            """
            Retrieves a DesignFormat type from the registry using a lookup
            string.

            :param name: The registered name of the Step. Case-insensitive.
            """
            return Self._registry.get(name)

        @classmethod
        def list(Self) -> List[str]:
            """
            :returns: A list of IDs of all registered DesignFormat.
            """
            return [cls.id for cls in Self._registry.values()]

    factory: ClassVar = DesignFormatFactory


# Common Design Formats
DesignFormat(
    "nl",
    "nl.v",
    "Verilog Netlist",
    "NETLIST",
).register()

DesignFormat(
    "pnl",
    "pnl.v",
    "Powered Verilog Netlist",
    "POWERED_NETLIST",
).register()

DesignFormat(
    "sdf_pnl",
    "sdf_pnl.v",
    "Powered Verilog Netlist for SDF Simulation (No Fills)",
    "POWERED_NETLIST_SDF_FRIENDLY",
    folder_override="pnl",
    alts=["pnl-sdf"],
).register()

DesignFormat(
    "npc_pnl",
    "npc_pnl.v",
    "Logical cell-only Powered Verilog Netlist",
    "LOGICAL_POWERED_NETLIST",
    folder_override="pnl",
).register()

DesignFormat(
    "def",
    "def",
    "Design Exchange Format",
    "DEF",
).register()

DesignFormat(
    "lef",
    "lef",
    "Library Exchange Format",
    "LEF",
).register()

DesignFormat(
    "sdc",
    "sdc",
    "Design Constraints",
    "SDC",
).register()

DesignFormat(
    "sdf",
    "sdf",
    "Standard Delay Format",
    "SDF",
    multiple=True,
).register()

DesignFormat(
    "spef",
    "spef",
    "Standard Parasitics Extraction Format",
    "SPEF",
    multiple=True,  # nom, min, max, ...
).register()

DesignFormat(
    "lib",
    "lib",
    "LIB Timing Library Format",
    "LIB",
    multiple=True,
).register()

DesignFormat(
    "spice",
    "spice",
    "Simulation Program with Integrated Circuit Emphasis",
    "SPICE",
).register()

DesignFormat(
    "gds",
    "gds",
    "GDSII Stream",
    "GDS",
).register()

DesignFormat(
    "vh",
    "vh",
    "Verilog Header",
    "VERILOG_HEADER",
).register()
