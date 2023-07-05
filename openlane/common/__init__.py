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
"""
Common Utilities Module
-----------------------

A number of common utility functions and classes used throughout the codebase.

.. no-imported-members
"""
from collections import UserString
import os
import re
import json
import typing
import pathlib
import unicodedata
from enum import Enum
from decimal import Decimal
from dataclasses import asdict, is_dataclass
from concurrent.futures import ThreadPoolExecutor

from typing import (
    Dict,
    Hashable,
    Iterator,
    List,
    Mapping,
    Sequence,
    Type,
    TypeVar,
    Tuple,
    Optional,
)


openlane_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_openlane_root() -> str:
    """
    Returns the root OpenLane folder, i.e., the folder containing the
    ``__init__.py``.
    """
    return openlane_root


def get_script_dir() -> str:
    """
    Gets the OpenLane tool `scripts` directory.

    :meta private:
    """
    return os.path.join(
        openlane_root,
        "scripts",
    )


def get_opdks_rev() -> str:
    """
    Gets the Open_PDKs revision confirmed compatible with this version of OpenLane.
    """
    return open(os.path.join(openlane_root, "open_pdks_rev"), encoding="utf8").read()


# The following code snippet has been adapted under the following license:
#
# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:

#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.

#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.

#     3. Neither the name of Django nor the names of its contributors may be used
#        to endorse or promote products derived from this software without
#        specific prior written permission.


# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
def slugify(value: str) -> str:
    """
    :param value: Input string
    :returns: The input string converted to lower case, with non-word
        (alphanumeric/underscore) characters removed, and spaces converted
        into hyphens.

        Leading and trailing whitespace is stripped.
    """
    value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    value = re.sub(r"[^\w\s\-\.]", "", value).strip().lower()
    return re.sub(r"[-\s\.]+", "-", value)


def protected(method):
    """A decorator to indicate protected methods.

    It dynamically adds a statement to the effect in the docstring as well
    as setting an attribute, ``is_internal``, to ``True``, but has no other effects.

    :param f: Method to mark as protected
    """
    if method.__doc__ is None:
        method.__doc__ = ""
    method.__doc__ = "**protected**\n" + method.__doc__

    setattr(method, "protected", True)
    return method


final = typing.final


def mkdirp(path: typing.Union[str, os.PathLike]):
    """
    Attempts to create a directory and all of its parents.

    Does not fail if the directory already exists, however, it does fail
    if it is unable to create any of the components and/or if the path
    already exists as a file.

    :param path: A filesystem path for the directory
    """
    return pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def StringEnum(name: str, values: Sequence[str]):
    """
    Creates a string enumeration class where the keys and values are the same.
    """
    return Enum(name, [(value, value) for value in values])


class GenericDictEncoder(json.JSONEncoder):
    """
    A JSON encoder for :class:`GenericDict` objects. Also handles some types not
    necessarily handled by the default JSON encoder, i.e., UserString, os.PathLike,
    Decimals, etcetera.

    It is recommended to use :meth:`GenericDict.to_json` unless you know what
    you're doing.
    """

    def default(self, o):
        if isinstance(o, GenericDict):
            return o.to_raw_dict()
        elif isinstance(o, os.PathLike) or isinstance(o, UserString):
            return str(o)
        elif is_dataclass(o):
            return asdict(o)
        elif isinstance(o, Enum):
            return o.name
        elif isinstance(o, Decimal):
            if o.as_integer_ratio()[1] == 1:
                return int(o)
            else:
                return float(o)
        return o


KT = TypeVar("KT", bound=Hashable)
VT = TypeVar("VT")


class GenericDict(Mapping[KT, VT]):
    """
    A dictionary with generic keys and values that is compatible with Python 3.8.

    :param copying: A base Mapping object to copy values from.
    :param overrides: Another mapping object to override the value from `copying`
        with.
    """

    _data: Dict[KT, VT]

    def __init__(
        self,
        copying: Optional[Mapping[KT, VT]] = None,
        /,
        overrides: Optional[Mapping[KT, VT]] = None,
    ) -> None:
        super().__init__()
        self._data = {}
        copying = copying or {}
        overrides = overrides or {}

        for key, value in copying.items():
            self._data[key] = value
        for key, value in overrides.items():
            self._data[key] = value

    def __getitem__(self, key: KT) -> VT:
        return self._data[key]

    def __setitem__(self, key: KT, item: VT):
        self._data[key] = item

    def __delitem__(self, key: KT):
        del self._data[key]

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return self.to_raw_dict().__repr__()

    def __iter__(self) -> Iterator[KT]:
        return iter(self._data)

    def pop(self, key: KT, /) -> VT:
        """
        :param key: The key to pop the value for.
        :returns: The value for key. Raises ``IndexError`` if the key does not
            exist. The key/value pair is then deleted from the dictionary.
        """
        value = self[key]
        del self[key]
        return value

    T = TypeVar("T", bound="GenericDict")

    def copy(self: T) -> T:
        """
        Convenience replacement for `object.__class__(object)`, which would
        create a copy of the ``GenericDict`` object.

        :returns: The copy
        """
        return self.__class__(self)

    def to_raw_dict(self) -> dict:
        """
        :returns: A copy of the underlying Python built-in ``dict`` for this class.
        """
        return self._data.copy()

    def get_encoder(self) -> Type[GenericDictEncoder]:
        """
        :returns: A JSON encoder handling GenericDict objects.
        """
        return GenericDictEncoder

    def keys(self):
        """
        :returns: A set-like object providing a view of the keys of the GenericDict object.
        """
        return self._data.keys()

    def values(self):
        """
        :returns: A set-like object providing a view of the values of the GenericDict object.
        """
        return self._data.values()

    def items(self):
        """
        :returns: A set-like object providing a view of the GenericDict object as (key, value) tuples.
        """
        return self._data.items()

    def dumps(self, **kwargs) -> str:
        """
        :param kwargs: Passed to ``json.dumps``.
        :returns: A JSON string representing the the GenericDict object.
        """
        if "indent" not in kwargs:
            kwargs["indent"] = 4
        return json.dumps(self.to_raw_dict(), cls=self.get_encoder(), **kwargs)

    def check(self, key: KT, /) -> Tuple[Optional[KT], Optional[VT]]:
        """
        Checks if a key exists and returns a tuple in the form ``(key, value)``.

        :param key: The key in question
        :returns: If the key does not exist, the value of ``key`` will be ``None`` and so will
            ``value``. If the key exists, ``key`` will be the key being checked for
            existence and ``value`` will be the value assigned to said key in the
            GenericDict object.

            Do note ``None`` is a valid value for some keys, so simply
            checking if the second element ``is not None`` is insufficient to check
            whether a key exists.
        """
        return (key if key in self._data else None, self.get(key))

    def update(self, incoming: "Mapping[KT, VT]"):
        """
        A convenience function to update multiple values in the GenericDict object
        at the same time.
        :param
        """
        for key, value in incoming.items():
            self[key] = value


class GenericImmutableDict(GenericDict[KT, VT]):
    _lock: bool

    def __init__(
        self,
        copying: Optional[Mapping[KT, VT]] = None,
        /,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(copying, *args, **kwargs)
        self._lock = True

    def __setitem__(self, key: KT, item: VT):
        if self._lock:
            raise TypeError(f"{self.__class__.__name__} is immutable")
        return super().__setitem__(key, item)


# Screw this, if you can figure out how to type hint mapping in dictionary out
# and non-mapping in sequence out in Python, be my guest
def copy_recursive(input):
    """
    Copies any arbitrarily-deep nested structure of Mappings and/or Sequences.

    :returns: The copy.

        All sequences will become built-in ``list``s and all mappings will
        become built-in ``dict``s.
    """

    def resolve_value(value):
        value_final = value
        if isinstance(value, Dict):
            value_final = copy_recursive(value)
        elif isinstance(value, List):
            value_final = copy_recursive(value)
        return value_final

    if isinstance(input, Mapping):  # Mappings are Sequences, but not vice versa
        dict_result = {}
        for key, value in input.items():
            dict_result[key] = resolve_value(value)
        return dict_result
    elif isinstance(input, Sequence):
        list_result = []
        for value in input:
            list_result.append(resolve_value(value))
        return list_result
    else:
        return input


T = TypeVar("T")


def idem(obj: T, *args, **kwargs) -> T:
    """
    :returns: the parameter ``obj`` unchanged. Useful for some lambdas.
    """
    return obj


TPE = ThreadPoolExecutor(max_workers=os.cpu_count())


def set_tpe(tpe: ThreadPoolExecutor):
    """
    Allows replacing OpenLane's global ``ThreadPoolExecutor`` with a customized
    one.

    :param tpe: The replacemend ThreadPoolExecutor
    """
    global TPE
    TPE = tpe


def get_tpe() -> ThreadPoolExecutor:
    """
    :returns: OpenLane's global ``ThreadPoolExecutor``
    """
    global TPE
    return TPE


## Metrics

modifier_rx = re.compile(r"([\w\-]+)\:([\w\-]+)$")


def parse_metric_modifiers(metric_name: str) -> Tuple[str, Mapping[str, str]]:
    """
    Parses a metric name into a base and modifiers as specified in
    the `Metrics4ML standard <https://github.com/ieee-ceda-datc/datc-rdf-Metrics4ML>`_.

    :param metric_name: The name of the metric as generated by a utility.
    :returns: A tuple of the base part as a string, then the modifiers as
        a key-value mapping.
    """
    mn_mut = metric_name.split("__")
    modifiers = {}
    i = len(mn_mut) - 1
    while match := modifier_rx.match(mn_mut[i]):
        mn_mut.pop()
        modifiers[match[1]] = match[2]
        i = i - 1
    return "__".join(mn_mut), modifiers
