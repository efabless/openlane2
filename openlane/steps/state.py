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
from collections import UserDict


class DesignFormat(Enum):
    """
    A list of design formats that may be kept in the state object.

    The value of the enum is a tuple. Currently, the tuple is of sized 1 and only
    has the extension of the files in question.
    """

    NETLIST = ("nl.v",)
    POWERED_NETLIST = ("pnl.v",)

    DEF = ("def",)
    LEF = ("lef",)
    ODB = ("odb",)

    SDF = ("sdf",)
    SPEF = ("spef",)
    LIB = ("lib",)

    GDSII = ("gds",)


class State(UserDict):
    """
    Basically, a dictionary with keys of type DesignFormat and string values,
    the string values being filesystem paths.

    The state is the only thing that can be altered by steps other than the
    filesystem.

    This dictionary has a property named `metrics` that also carries statistics
    about the design: area, wire length, et cetera.
    """

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
