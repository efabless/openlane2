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

import os
import json
import shutil
from decimal import Decimal
from collections import UserString
from typing import Iterator, List, Mapping, TypeVar, Union, Optional, Dict, Any

from .design_format import DesignFormat, DesignFormatObject
from ..common import mkdirp


class Path(UserString, os.PathLike):
    """
    A Path type for OpenLane configuration variables.

    Basically just a string.
    """

    def __fspath__(self) -> str:
        return str(self)

    def exists(self) -> bool:
        """
        A convenience method calling :meth:`os.path.exists`
        """
        return os.path.exists(self)


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


VT = Union[Path, Dict[str, Path], None]


class State(Mapping[str, VT]):
    """
    Basically, a dictionary with keys of type :class:`DesignFormat` and values
    of (nested dictionaries of) :class:`Path`.

    The state is the only thing that can be altered by steps other than the
    filesystem.

    :attr metrics: A dictionary that carries statistics about the design: area,
        wire length, et cetera, but also miscellaneous data, for example, whether
        it passed a certain check or not.
    """

    _data: dict

    metrics: dict

    def __init__(self, metrics: Optional[dict] = None) -> None:
        super().__init__()
        self._data = {}
        for format in DesignFormat:
            self[format] = None
        self.metrics = metrics or {}

    def __getitem__(self, key: Union[DesignFormat, str]) -> VT:
        if isinstance(key, DesignFormat):
            id: str = key.value.id
            key = id
        return self._data[key]

    def __setitem__(self, key: Union[DesignFormat, str], item: VT):
        if isinstance(key, DesignFormat):
            id: str = key.value.id
            key = id
        self._data[key] = item

    def _as_dict(self, metrics: bool = True) -> Dict[str, Any]:
        final: Dict[Any, Any] = dict(self)
        if metrics:
            final["metrics"] = self.metrics
        return final

    T = TypeVar("T", Dict, List)

    def __copy_recursive__(self, input: T) -> T:
        def resolve_value(value):
            value_final = value
            if isinstance(value, dict):
                value_final = self.__copy_recursive__(value)
            elif isinstance(value, list):
                value_final = self.__copy_recursive__(value)
            return value_final

        if isinstance(input, list):
            result = []
            for value in input:
                result.append(resolve_value(value))
            return result
        else:
            result = {}
            for key, value in input.items():
                result[key] = resolve_value(value)
            return result

    def copy(self: "State") -> "State":
        new = State()
        new._data = self.__copy_recursive__(self._data)
        new.metrics = self.__copy_recursive__(self.metrics)
        return new

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return self._as_dict().__repr__()

    def dumps(self, **kwargs) -> str:
        """
        Dumps data as JSON.
        """
        if "indent" not in kwargs:
            kwargs["indent"] = 4
        return json.dumps(self._as_dict(), cls=StateEncoder, **kwargs)

    def _save_snapshot_recursive(
        self,
        path: Union[str, os.PathLike],
        views: Union[Dict, "State"],
        key_path: str = "",
    ):
        mkdirp(path)
        for key, value in views.items():
            current_key_path = f"{key_path}.{key}"
            if value is None:
                continue
            current_folder = key.strip("*")
            if df := DesignFormat.by_id(key):
                # For type-checker: all guaranteed to be DesignFormatObjects
                assert isinstance(df.value, DesignFormatObject)
                current_folder = df.value.folder

            if isinstance(value, dict):
                subdirectory = os.path.join(path, current_folder)
                self._save_snapshot_recursive(
                    subdirectory,
                    value,
                    key_path=current_key_path,
                )
            else:
                target_dir = os.path.join(
                    path,
                    current_folder,
                )
                mkdirp(target_dir)
                target_path = os.path.join(target_dir, os.path.basename(value))
                shutil.copyfile(value, target_path, follow_symlinks=True)

    def save_snapshot(self, path: Union[str, os.PathLike]):
        """
        Validates the current state then saves all views to a folder by
        design format, including the metrics.

        :param path: The folder that would contain other folders.
        """
        self.validate()
        self._save_snapshot_recursive(path, self)
        metrics_path = os.path.join(path, "metrics.csv")
        with open(metrics_path, "w") as f:
            f.write("Metric,Value\n")
            for metric in self.metrics:
                f.write(f"{metric}, {self.metrics[metric]}\n")

    def _validate_recursive(
        self,
        views: Dict,
        key_path: str = "",
        depth: int = 0,
    ):
        for key, value in views.items():
            current_key_path = f"{key_path}.{key}"
            if depth == 0 and DesignFormat.by_id(key) is None:
                raise InvalidState(
                    f"Key {current_key_path} does not match a known design format."
                )
            if value is not None:
                if isinstance(value, Path):
                    if not value.exists():
                        raise InvalidState(
                            f"Path for format {current_key_path} does not exist: '{value}'."
                        )
                elif isinstance(value, dict):
                    self._validate_recursive(
                        value, key_path=current_key_path, depth=depth + 1
                    )
                else:
                    raise InvalidState(
                        f"Value for format '{current_key_path}' is not a Path nor a dictionary of strings to Paths: '{value}'."
                    )

    def validate(self):
        """
        Ensures that all paths exist in a State.
        """
        self._validate_recursive(self._as_dict(metrics=False))

    @classmethod
    def _loads_recursive(
        Self,
        target: Union[Dict, "State"],
        views: Union[Dict, "State"],
        validate_path: bool = True,
        key_path: str = "",
    ):
        for key, value in views.items():
            current_key_path = f"{key_path}.{key}"
            if value is None:
                target[key] = value
                continue

            if isinstance(value, dict):
                all_values: Dict = {}
                Self._loads_recursive(
                    all_values,
                    value,
                    validate_path,
                    key_path=current_key_path,
                )
                target[key] = all_values
            else:
                if validate_path and not os.path.exists(value):
                    raise ValueError(
                        f"Provided path '{value}' to design format '{current_key_path}' does not exist."
                    )
                target[key] = Path(value)

    @classmethod
    def loads(Self, json_in: str, validate_path: bool = True) -> "State":
        raw = json.loads(json_in, parse_float=Decimal)

        metrics = raw.get("metrics")
        if metrics is not None:
            del raw["metrics"]

        state = Self(metrics=metrics)

        Self._loads_recursive(state, raw, validate_path)

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
