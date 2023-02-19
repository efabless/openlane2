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
from enum import Enum
from decimal import Decimal
from collections import UserDict, UserString
from typing import Any, Tuple, Union, List

from dataclasses import dataclass, asdict


@dataclass
class Meta:
    version: int
    flow: Union[str, List[str]] = "Classic"


class Path(UserString, os.PathLike):
    """
    A Path type for OpenLane configuration variables.

    Basically just a string.
    """

    def __fspath__(self) -> str:
        return str(self)

    def exists(self) -> bool:
        """
        A convenience method calling :py:attr:`os.path.exists`
        """
        return os.path.exists(self)


class ConfigEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Meta):
            return asdict(o)
        elif isinstance(o, Decimal):
            if o.as_integer_ratio()[1] == 1:
                return int(o)
            else:
                return float(o)
        elif isinstance(o, Path):
            return str(o)
        elif isinstance(o, Enum):
            return str(o)
        return super(ConfigEncoder, self).default(o)


class Config(UserDict):
    """
    A map from OpenLane configuration variable keys to their values.

    It is recommended that you construct these using the :class:`ConfigBuilder`
    singleton class.
    """

    meta = Meta(version=1)

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

            Do note :code:`None` is a valid value, so simply checking if the
            second element :code:`is not None` is invalid to check whether
            a key exists.
        """
        return (key in self.keys(), self.get(key))

    def extract(self, key: str) -> Tuple[bool, Any]:
        """
        A mutating method that attempts to find a key, and, if it exists,
        deletes it from the configuration object and returns its value.

        :param key: A string key representing an OpenLane configuration variable.
        :returns: A tuple of whether that key existed, and if so its value.

            Do note :code:`None` is a valid value, so simply checking if the
            second element :code:`is not None` is invalid to check whether
            a key exists.
        """
        found, value = self.check(key)
        if found:
            del self[key]
        return (found, value)
