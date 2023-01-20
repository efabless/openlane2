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
        self.metrics = dict()

    def __copy__(self: "State") -> "State":
        new = super().__copy__()
        new.metrics = self.metrics.copy()
        return new

    def __repr__(self) -> str:
        representable = dict(self)
        representable["metrics"] = self.metrics
        return representable.__repr__()
