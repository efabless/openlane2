from enum import Enum
from typing import NamedTuple
from typing import NamedTuple
from collections import UserDict


class DesignFormat(Enum):
    NETLIST = ("nl.v",)
    POWERED_NETLIST = ("pnl.v",)

    DEF = ("def",)
    LEF = ("lef",)
    ODB = ("odb",)

    SPEF = ("spef",)
    LIB = ("lib",)

    GDSII = ("gds",)


class Objects(Enum):
    MERGED_LEF = (".lef",)
    MERGED_LIB = (".lib",)


class Output(NamedTuple):
    format: DesignFormat
    update: bool = True


class State(UserDict):
    metrics: dict

    def __init__(self) -> None:
        super().__init__()
        for format in DesignFormat:
            self[format] = None
        self.metrics = {}
