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
import json
from decimal import Decimal
from collections import UserDict
from typing import Union, Optional

from .design_format import DesignFormat

from ..config import Path


class StateEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o.as_integer_ratio()[1] == 1:
                return int(o)
            else:
                return float(o)
        elif isinstance(o, Path):
            return str(o)
        return super(StateEncoder, self).default(o)


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
            self[format.name] = None
        self.metrics = dict()

    def __getitem__(self, key: Union[DesignFormat, str]) -> Optional[Path]:
        if isinstance(key, DesignFormat):
            key = key.name
        return super().__getitem__(key)

    def __setitem__(self, key: Union[DesignFormat, str], item: Path):
        if isinstance(key, DesignFormat):
            key = key.name
        return super().__setitem__(key, item)

    def as_dict(self) -> dict:
        final = dict(self)
        final["metrics"] = self.metrics
        return final

    def __copy__(self: "State") -> "State":
        new = super().__copy__()
        new.metrics = self.metrics.copy()
        return new

    def __repr__(self) -> str:
        return self.as_dict().__repr__()

    def dumps(self, **kwargs) -> str:
        if "indent" not in kwargs:
            kwargs["indent"] = 4
        return json.dumps(self.as_dict(), cls=StateEncoder, **kwargs)
