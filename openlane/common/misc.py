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
import re
import sys
import typing
import pathlib
import unicodedata
from collections import UserString
from typing import (
    Any,
    ClassVar,
    Iterable,
    TypeVar,
    Optional,
    Union,
    Tuple,
)


T = TypeVar("T")


def idem(obj: T, *args, **kwargs) -> T:
    """
    :returns: the parameter ``obj`` unchanged. Useful for some lambdas.
    """
    return obj


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
    return (
        open(os.path.join(get_openlane_root(), "open_pdks_rev"), encoding="utf8")
        .read()
        .strip()
    )


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
    as setting an attribute, ``protected``, to ``True``, but has no other effects.

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


class Path(UserString, os.PathLike):
    """
    A Path type for OpenLane configuration variables.

    Basically just a string.
    """

    # This path will pass the validate() call, but will
    # fail to open. It should be used for deprecated variable
    # translation only.
    _dummy_path: ClassVar[str] = "__openlane_dummy_path"

    def __fspath__(self) -> str:
        return str(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}('{self}')"

    def exists(self) -> bool:
        """
        A convenience method calling :meth:`os.path.exists`
        """
        return os.path.exists(self)

    def validate(self):
        """
        Raises an error if the path does not exist.
        """
        if not self.exists() and not self == Path._dummy_path:
            raise ValueError(f"'{self}' does not exist")

    def startswith(
        self,
        prefix: Union[str, Tuple[str, ...], UserString, os.PathLike],
        start: Optional[int] = 0,
        end: Optional[int] = sys.maxsize,
    ) -> bool:
        if isinstance(prefix, UserString) or isinstance(prefix, os.PathLike):
            prefix = str(prefix)
        return super().startswith(prefix, start, end)

    def rel_if_child(
        self,
        start: Union[str, os.PathLike] = os.getcwd(),
        *,
        relative_prefix: str = "",
    ) -> "Path":
        my_abspath = os.path.abspath(self)
        start_abspath = os.path.abspath(start)
        if my_abspath.startswith(start_abspath):
            return Path(relative_prefix + os.path.relpath(self, start_abspath))
        else:
            return Path(my_abspath)


class zip_first(object):
    """
    Works like ``zip_longest`` if ｜a｜ > ｜b｜ and ``zip`` if ｜a｜ <= ｜b｜.
    """

    def __init__(self, a: Iterable, b: Iterable, fillvalue: Any) -> None:
        self.a = a
        self.b = b
        self.fillvalue = fillvalue

    def __iter__(self):
        self.iter_a = iter(self.a)
        self.iter_b = iter(self.b)
        return self

    def __next__(self):
        a = next(self.iter_a)
        b = self.fillvalue
        try:
            b = next(self.iter_b)
        except StopIteration:
            pass
        return (a, b)


def format_size(byte_count: int) -> str:
    units = [
        "B",
        "KiB",
        "MiB",
        "GiB",
        "TiB",
        "PiB",
        "EiB",
        # TODO: update OpenLane when zebibytes are a thing
    ]

    tracker = 0
    so_far = byte_count
    while (so_far // 1024) > 0 and tracker < (len(units) - 1):
        tracker += 1
        so_far //= 1024

    return f"{so_far}{units[tracker]}"


def format_elapsed_time(elapsed_seconds: float) -> str:
    hours = int(elapsed_seconds // 3600)
    leftover = elapsed_seconds % 3600

    minutes = int(leftover // 60)
    leftover = leftover % 60

    seconds = int(leftover // 1)
    milliseconds = int((leftover % 1) * 1000)

    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"
