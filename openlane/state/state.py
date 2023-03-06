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
import os
import json
from decimal import Decimal
from collections import UserDict
from typing import Union, Optional, Dict, Any

from .design_format import DesignFormat, DesignFormatByID

from ..config import Path
from ..common import warn


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


class StateDecoder(json.JSONDecoder):
    def default(self, o):
        if isinstance(o, float) or isinstance(o, int):
            return Decimal(o)
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

    def __init__(self, metrics: Optional[dict] = None) -> None:
        super().__init__()
        for format in DesignFormat:
            id: str = format.value[0]
            self[id] = None
        self.metrics = metrics or {}

    def __getitem__(self, key: Union[DesignFormat, str]) -> Optional[Path]:
        if isinstance(key, DesignFormat):
            id: str = key.value[0]
            key = id
        return super().__getitem__(key)

    def __setitem__(self, key: Union[DesignFormat, str], item: Optional[Path]):
        if isinstance(key, DesignFormat):
            id: str = key.value[0]
            key = id
        return super().__setitem__(key, item)

    def as_dict(self) -> dict:
        final: Dict[Any, Any] = dict(self)
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

    @classmethod
    def loads(Self, json_in: str, validate_path: bool = True) -> "State":
        raw = json.loads(json_in, cls=StateDecoder)

        metrics = raw.get("metrics")
        if metrics is not None:
            del raw["metrics"]

        state = Self(metrics=metrics)

        for key, value in raw.items():
            df = DesignFormatByID.get(key)
            if df is None:
                warn(f"Unknown design format ID '{key}' in loaded state.")
                continue

            if value is None:
                state[df] = value
                continue

            if validate_path and not os.path.exists(value):
                raise ValueError(
                    f"Provided path '{value}' to design format '{key}' does not exist."
                )
            state[df] = Path(value)

        return state

    def _repr_html_(self) -> str:
        result = """
        <div style="display: grid; grid-auto-columns: minmax(0, 1fr); grid-auto-rows: minmax(0, 1fr); grid-auto-flow: column;">
            <table style="grid-column-start: 1; grid-column-end: 2;">
                <tr>
                    <th>Format</th>
                    <th>Path</th>
                </tr>
        """
        for id, value in dict(self).items():
            assert isinstance(id, str)
            if value is None:
                continue

            format = DesignFormatByID[id]

            value_rel = os.path.relpath(value, ".")

            result += f"""
                <tr>
                    <td>{format.value[2]}</td>
                    <td><a href="{value_rel}">{value_rel}</a></td>
                </tr>
            """

        result += """
            </table>
        </div>
        """

        return result
