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
import sys
import json
import shutil
from decimal import Decimal
from typing import List, Mapping, Tuple, Union, Optional, Dict, Any

from ..common import (
    Path,
    GenericImmutableDict,
    mkdirp,
    copy_recursive,
    DesignFormat,
    DesignFormatObject,
)


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
        copying: Optional[
            Union[Mapping[str, StateElement], Mapping[DesignFormat, StateElement]]
        ] = None,
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
                if isinstance(key, DesignFormat):
                    copying_resolved[key.value.id] = value
                else:
                    copying_resolved[key] = value

        for format in DesignFormat:
            assert isinstance(format.value, DesignFormatObject)  # type checker shut up
            if format.value.id not in copying_resolved:
                copying_resolved[format.value.id] = None

        overrides_resolved = {}
        if o_mapping := overrides:
            for k, value in o_mapping.items():
                if isinstance(k, DesignFormat):
                    assert isinstance(
                        k.value, DesignFormatObject
                    )  # type checker shut up
                    k = k.value.id
                overrides_resolved[k] = value

        self.metrics = GenericImmutableDict(metrics or {})

        super().__init__(
            copying_resolved,
            *args,
            overrides=overrides_resolved,
            **kwargs,
        )

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
        final = super().to_raw_dict()
        if metrics:
            final["metrics"] = self.metrics.to_raw_dict()
        return final

    def copy(self: "State") -> "State":
        metrics: GenericImmutableDict[str, Any] = GenericImmutableDict(
            copy_recursive(self.metrics)
        )
        new = State(self, metrics=metrics)
        return new

    def __save_snapshot_recursive(
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
                self.__save_snapshot_recursive(
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
        self.__save_snapshot_recursive(path, self)
        metrics_csv_path = os.path.join(path, "metrics.csv")
        with open(metrics_csv_path, "w", encoding="utf8") as f:
            f.write("Metric,Value\n")
            for metric in self.metrics:
                f.write(f"{metric},{self.metrics[metric]}\n")

        metrics_json_path = os.path.join(path, "metrics.json")
        with open(metrics_json_path, "w", encoding="utf8") as f:
            f.write(self.metrics.dumps())

    def __validate_recursive(
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
                    self.__validate_recursive(
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
        self.__validate_recursive(self.to_raw_dict(metrics=False))

    @classmethod
    def __loads_recursive(
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
                target[key] = Self.__loads_recursive(
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
        try:
            raw = json.loads(json_in, parse_float=Decimal)
        except json.JSONDecodeError as e:
            raise InvalidState(f"Invalid JSON string provided for state: {e}")

        if not isinstance(raw, dict):
            raise InvalidState("Failed to load state: JSON result is not a dictionary")

        metrics = raw.get("metrics")
        if metrics is not None:
            del raw["metrics"]

        views = Self.__loads_recursive(raw, validate_path)
        state = Self(views, metrics=metrics)

        return state

    def __mapping_to_html_rec(
        self,
        mapping: Mapping[str, Any],
        header_optional: Optional[Tuple[str, str]] = None,
    ):
        result = """
        <table style="grid-column-start: 1; grid-column-end: 2; ">
        """
        if header := header_optional:
            key_h, value_h = header
            result += f"""
                <tr>
                    <th style="text-align: left;">{key_h}</th>
                    <th style="text-align: left;">{value_h}</th>
                </tr>
            """

        for id, value in mapping.items():
            if value is None:
                continue

            key_content = id
            if format := DesignFormat.by_id(id):
                key_content = format.value.id

            value_content = str(value)
            if isinstance(value, Mapping):
                value_content = self.__mapping_to_html_rec(value)
            elif isinstance(value, Path):
                value_rel = os.path.relpath(value, ".")

                value_content = f'<a href="{value_rel}">{value_rel}</a>'
                if "google.colab" in sys.modules:
                    # Can't link in colab
                    value_content = value_rel

            result += f"""
                <tr>
                    <td style="text-align: left;">{key_content}</td>
                    <td style="text-align: left;">{value_content}</td>
                </tr>
            """

        result += """
        </table>
        """
        return result

    def _repr_html_(self) -> str:
        return (
            '<div style="display: grid; grid-auto-columns: minmax(0, 1fr); grid-auto-rows: minmax(0, 1fr); grid-auto-flow: column;">'
            + self.__mapping_to_html_rec(
                self.to_raw_dict(metrics=False),
                ("Format", "Path"),
            )
            + "</div>"
        )
