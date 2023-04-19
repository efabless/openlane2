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
import shutil
from decimal import Decimal
from collections import UserDict
from typing import Union, Optional, Dict, Any

from .design_format import DesignFormat

from ..config import Path
from ..common import mkdirp
from ..logging import warn


class InvalidState(RuntimeError):
    pass


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

    :attr metrics: A dictionary that carries statistics about the design: area,
        wire length, et cetera, but also miscellaneous data, for example, whether
        it passed a certain check or not.
    """

    metrics: dict

    def __init__(self, metrics: Optional[dict] = None) -> None:
        super().__init__()
        for format in DesignFormat:
            id: str = format.value.id
            self[id] = None
        self.metrics = metrics or {}

    def __getitem__(self, key: Union[DesignFormat, str]) -> Optional[Path]:
        if isinstance(key, DesignFormat):
            id: str = key.value.id
            key = id
        return super().__getitem__(key)

    def __setitem__(self, key: Union[DesignFormat, str], item: Optional[Path]):
        if isinstance(key, DesignFormat):
            id: str = key.value.id
            key = id
        return super().__setitem__(key, item)

    def _as_dict(self, metrics: bool = True) -> dict:
        final: Dict[Any, Any] = dict(self)
        if metrics:
            final["metrics"] = self.metrics
        return final

    def __copy__(self: "State") -> "State":
        new = super().__copy__()
        new.metrics = self.metrics.copy()
        return new

    def __repr__(self) -> str:
        return self._as_dict().__repr__()

    def dumps(self, **kwargs) -> str:
        """
        Dumps data as JSON.
        """
        if "indent" not in kwargs:
            kwargs["indent"] = 4
        return json.dumps(self._as_dict(), cls=StateEncoder, **kwargs)

    def save_snapshot(self, path: Union[str, os.PathLike]):
        mkdirp(path)
        self.validate()
        for key, value in self.items():
            assert isinstance(key, str)
            if value is None:
                continue
            target_dir = os.path.join(path, key)
            mkdirp(target_dir)
            target_path = os.path.join(target_dir, os.path.basename(value))
            shutil.copyfile(value, target_path, follow_symlinks=True)
        metrics_path = os.path.join(path, "metrics.csv")
        with open(metrics_path, "w") as f:
            f.write("Metric,Value\n")
            for metric in self.metrics:
                f.write(f"{metric}, {self.metrics[metric]}\n")

    def validate(self):
        for key, value in self._as_dict(metrics=False).items():
            if DesignFormat.by_id(key) is None:
                raise InvalidState(f"Key {key} does not match a known design format.")
            if value is not None:
                if not isinstance(value, Path):
                    raise InvalidState(
                        f"Value for format {key} is not a openlane.config.Path object: '{value}'."
                    )
                if not os.path.exists(str(value)):
                    raise InvalidState(
                        f"Value for format {key} does not exist: '{value}'."
                    )

    @classmethod
    def loads(Self, json_in: str, validate_path: bool = True) -> "State":
        raw = json.loads(json_in, cls=StateDecoder)

        metrics = raw.get("metrics")
        if metrics is not None:
            del raw["metrics"]

        state = Self(metrics=metrics)

        for key, value in raw.items():
            df = DesignFormat.by_id(key)
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
        for id, value in self._as_dict(metrics=False).items():
            assert isinstance(id, str)
            if value is None:
                continue

            format = DesignFormat.by_id(id)
            assert format is not None

            value_rel = os.path.relpath(value, ".")

            result += f"""
                <tr>
                    <td>{format.value.id}</td>
                    <td><a href="{value_rel}">{value_rel}</a></td>
                </tr>
            """

        result += """
            </table>
        </div>
        """

        return result
