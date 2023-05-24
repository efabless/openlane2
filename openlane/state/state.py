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
from typing import List, Mapping, Union, Optional, Dict, Any

from .design_format import DesignFormat, DesignFormatObject

from ..common import GenericImmutableDict, mkdirp, copy_recursive


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


StateElement = Union[Path, List[Path], Dict[str, Union[Path, List[Path]]], None]


class State(GenericImmutableDict[str, StateElement]):
    """
    Basically, a dictionary from :class:`DesignFormat`s and values
    of (nested dictionaries of) :class:`Path`.

    The state is the only thing that can be altered by steps other than the
    filesystem.

    :attr metrics: A dictionary that carries statistics about the design: area,
        wire length, et cetera, but also miscellaneous data, for example, whether
        it passed a certain check or not.
    """

    metrics: GenericImmutableDict[str, Any]

    def __init__(
        self,
        copying: Optional[Mapping[str, StateElement]] = None,
        *args,
        overrides: Optional[
            Union[Mapping[str, StateElement], Mapping[DesignFormat, StateElement]]
        ] = None,
        metrics: Optional[Mapping[str, Any]] = None,
        **kwargs,
    ) -> None:
        copying_resolved: Dict[str, StateElement] = {}
        if c_mapping := copying:
            for key, value in c_mapping.items():
                copying_resolved[key] = value

        for format in DesignFormat:
            assert isinstance(format.value, DesignFormatObject)  # type checker shut up
            if format.value.id not in copying_resolved:
                copying_resolved[format.value.id] = None

        overrides_resolved = {}
        if o_mapping := overrides:
            for key, value in o_mapping.items():
                if isinstance(key, DesignFormat):
                    assert isinstance(
                        key.value, DesignFormatObject
                    )  # type checker shut up
                    key = key.value.id
                overrides_resolved[key] = value

        super().__init__(
            copying_resolved,
            *args,
            overrides=overrides_resolved,
            **kwargs,
        )

        self.metrics = GenericImmutableDict(metrics or {})

    def __getitem__(self, key: Union[DesignFormat, str]) -> StateElement:
        if isinstance(key, DesignFormat):
            id: str = key.value.id
            key = id
        return super().__getitem__(key)

    def __setitem__(self, key: Union[DesignFormat, str], item: StateElement):
        if isinstance(key, DesignFormat):
            id: str = key.value.id
            key = id
        return super().__setitem__(key, item)

    def __delitem__(self, key: Union[DesignFormat, str]):
        if isinstance(key, DesignFormat):
            id: str = key.value.id
            key = id
        return super().__delitem__(key)

    def to_raw_dict(self, metrics: bool = True) -> Dict[str, Any]:
        final: Dict[Any, Any] = self._data.copy()
        if metrics:
            final["metrics"] = self.metrics
        return final

    def copy(self: "State") -> "State":
        new = State()
        new._data = copy_recursive(self._data)
        new.metrics = copy_recursive(self.metrics)
        return new

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
        self._validate_recursive(self.to_raw_dict(metrics=False))

    @classmethod
    def _loads_recursive(
        Self,
        views: Dict,
        validate_path: bool = True,
        key_path: str = "",
    ) -> dict:
        target: dict = {}
        for key, value in views.items():
            current_key_path = f"{key_path}.{key}"
            if value is None:
                target[key] = value
                continue

            if isinstance(value, dict):
                target[key] = Self._loads_recursive(
                    value,
                    validate_path,
                    key_path=current_key_path,
                )
            else:
                if validate_path and not os.path.exists(value):
                    raise ValueError(
                        f"Provided path '{value}' to design format '{current_key_path}' does not exist."
                    )
                target[key] = Path(value)
        return target

    @classmethod
    def loads(Self, json_in: str, validate_path: bool = True) -> "State":
        raw = json.loads(json_in, parse_float=Decimal)
        if not isinstance(raw, dict):
            raise InvalidState("Failed to load state: JSON result is a dictionary")

        metrics = raw.get("metrics")
        if metrics is not None:
            del raw["metrics"]

        views = Self._loads_recursive(raw, validate_path)
        state = Self(views, metrics=metrics)

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
        for id, value in self.to_raw_dict(metrics=False).items():
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
