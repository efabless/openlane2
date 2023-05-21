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
import yaml
from enum import Enum
from decimal import Decimal
from textwrap import dedent
from dataclasses import dataclass, asdict, is_dataclass
from collections import UserDict
from typing import (
    Any,
    ClassVar,
    Tuple,
    Union,
    List,
    Optional,
    Sequence,
)

from ..state import Path


def StringEnum(name: str, values: Sequence[str]):
    """
    Creates a string enumeration where the keys and values are the same.
    """
    return Enum(name, [(value, value) for value in values])


@dataclass
class Meta:
    version: int = 1
    flow: Union[None, str, List[str]] = "Classic"


class ConfigEncoder(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        elif isinstance(o, Decimal):
            if o.as_integer_ratio()[1] == 1:
                return int(o)
            else:
                return float(o)
        elif isinstance(o, Path):
            return str(o)
        elif isinstance(o, Enum):
            return o.value
        return super(ConfigEncoder, self).default(o)


class Config(UserDict):
    """
    A map from OpenLane configuration variable keys to their values.

    It is recommended that you construct these using the :class:`ConfigBuilder`
    singleton class.

    A created Config is immutable and cannot be modified by Steps.
    """

    current_interactive: ClassVar[Optional["Config"]] = None
    locked: bool = False

    meta: Meta = Meta(version=1)
    interactive: bool = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.locked = True

    def _unlock(self) -> "Config":
        self.locked = False
        return self

    def _lock(self) -> "Config":
        self.locked = True
        return self

    @classmethod
    def get_meta(
        Self,
        json_config_in: Union[str, os.PathLike],
        flow_override: Optional[str] = None,
    ) -> Optional[Meta]:
        """
        Returns the Meta object of a JSON configuration file

        :param config_in: A configuration file.
        :returns: Either a Meta object, or if the file is not a JSON file, None.
        """
        try:
            obj = json.load(open(json_config_in, encoding="utf8"))
        except (json.JSONDecodeError, IsADirectoryError):
            return None

        meta = Meta()
        if meta_raw := obj.get("meta"):
            meta = Meta(**meta_raw)

        if flow_override is not None:
            meta.flow = flow_override

        return meta

    def copy(self, **overrides) -> "Config":
        """
        Produces a shallow copy of the configuration object.

        :param overrides: A series of configuration overrides as key-value pairs.
            These values are NOT validated and you should not be overriding these
            haphazardly.
        """
        import copy

        data = self.data
        try:
            self.data = {}
            c = copy.copy(self)
        finally:
            self.data = data
        c._unlock()
        c.update(self)
        c.update(overrides)
        c._lock()
        return c

    def __setitem__(self, key: str, item: Any):
        if self.locked:
            raise AttributeError("Config objects are immutable.")

        return super().__setitem__(key, item)

    def dumps(self) -> str:
        """
        :returns: A JSON string representing the configuration object.
        """
        data = self.data.copy()
        data["meta"] = self.meta
        return json.dumps(data, indent=2, cls=ConfigEncoder, sort_keys=True)

    def check(self, key: str) -> Tuple[bool, Any]:
        """
        :param key: A string key representing an OpenLane configuration variable.
        :returns: A tuple of whether that key exists, and if so, its value.

            Do note ``None`` is a valid value, so simply checking if the
            second element ``is not None`` is invalid to check whether
            a key exists.
        """
        return (key in self.keys(), self.get(key))

    def extract(self, key: str) -> Tuple[bool, Any]:
        """
        A mutating method that attempts to find a key, and, if it exists,
        deletes it from the configuration object and returns its value.

        :param key: A string key representing an OpenLane configuration variable.
        :returns: A tuple of whether that key existed, and if so its value.

            Do note ``None`` is a valid value, so simply checking if the
            second element ``is not None`` is invalid to check whether
            a key exists.
        """
        found, value = self.check(key)
        if found:
            del self[key]
        return (found, value)

    def _repr_markdown_(self) -> str:
        title = "Interactive Configuration" if self.interactive else "Configuration"
        values_title = "Initial Values" if self.interactive else "Values"
        return (
            dedent(
                f"""
                ### {title}
                #### {values_title}

                <br />

                ```yml
                %s
                ```
                """
            )
            % yaml.safe_dump(json.loads(self.dumps()))
        )
