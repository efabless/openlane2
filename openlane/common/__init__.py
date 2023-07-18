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
import os
import re
import typing
import pathlib
import unicodedata
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

from typing import (
    Mapping,
    Sequence,
    TypeVar,
    Tuple,
)

from .generic_dict import (
    GenericDictEncoder,
    GenericDict,
    GenericImmutableDict,
    copy_recursive,
    is_string,
)


def get_openlane_root() -> str:
    """
    Returns the root OpenLane folder, i.e., the folder containing the
    ``__init__.py``.
    """
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_script_dir() -> str:
    """
    Gets the OpenLane tool `scripts` directory.

    :meta private:
    """
    return os.path.join(
        get_openlane_root(),
        "scripts",
    )


def get_opdks_rev() -> str:
    """
    Gets the Open_PDKs revision confirmed compatible with this version of OpenLane.
    """
    return open(
        os.path.join(get_openlane_root(), "open_pdks_rev"), encoding="utf8"
    ).read()


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
    :returns: The input string converted to lower case, with all characters
        except alphanumerics, underscores and hyphens removed, and spaces and\
        dots converted into hyphens.

        Leading and trailing whitespace is stripped.
    """
    value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    value = re.sub(r"[^\w\s\-\.]", "", value).strip().lower()
    return re.sub(r"[\s\.]+", "-", value)


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


T = TypeVar("T")


def idem(obj: T, *args, **kwargs) -> T:
    """
    :returns: the parameter ``obj`` unchanged. Useful for some lambdas.
    """
    return obj


## TPE

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

modifier_rx = re.compile(r"([\w\-]+)\:([\w\-]+)")


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
    if ":" in mn_mut[i]:
        modifier_list = mn_mut[i].split(":")
        if len(modifier_list) % 2 == 0:
            for i in range(0, len(modifier_list) - 1, 2):
                modifiers[modifier_list[i]] = modifier_list[i + 1]
            mn_mut.pop()
    return "__".join(mn_mut), modifiers
