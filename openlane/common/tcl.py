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
import tkinter
from typing import Dict, Mapping, Any, Iterable

_setter_rx = re.compile(r"set\s+(?:\:\:)?env\(\s*(\w+)\s*\)")
_find_unsafe = re.compile(r"[^\w@%+=:,./-]", re.ASCII).search
_escapes_in_quotes = re.compile(r"([\\\$\"\[])")


class TclUtils(object):
    """
    A collection of useful Tcl utilities.
    """

    def __init__(self):
        raise TypeError(f"Cannot create instances of '{self.__class__.__name__}'")

    @staticmethod
    def escape(s: str) -> str:
        """
        :returns: If the string can be parsed by Tcl as a single token, the string
            is returned verbatim.

            Otherwise, the string is returned in double quotes, with any unsafe
            characters escaped with a backslash.
        """
        if s == "":
            return '""'
        if not _find_unsafe(s):
            return s
        return '"' + _escapes_in_quotes.sub(r"\\\1", s).replace("\n", r"\n") + '"'

    @staticmethod
    def join(ss: Iterable[str]) -> str:
        """
        :param ss: Input list
        :returns: The input list converted to a Tcl-compatible list where each
            element is either a single token or double-quoted (i.e. interpreted
            by Tcl as a single element.)
        """
        return " ".join(TclUtils.escape(arg) for arg in ss)

    @staticmethod
    def _eval_env(env_in: Mapping[str, Any], tcl_in: str) -> Dict[str, Any]:
        interpreter = tkinter.Tcl()
        keys_modified = _setter_rx.findall(tcl_in)

        env_out = dict(env_in)
        rollback = {}
        for key, value in env_in.items():
            rollback[key] = os.getenv(key)
            os.environ[key] = str(value)

        tcl_script = f"""
        {tcl_in}
        set counter 0
        foreach key [array names ::env] {{
            set "key$counter" $key
            set "value$counter" $::env($key)
            incr counter
        }}
        """
        interpreter.eval(tcl_script)

        for key, value in rollback.items():
            if value is not None:
                os.environ[key] = value
            else:
                del os.environ[key]

        counter = 0
        while True:
            key_var = f"key{counter}"
            value_var = f"value{counter}"

            try:
                key = interpreter.getvar(key_var)
            except tkinter.TclError:
                break
            value = interpreter.getvar(value_var)
            if key in keys_modified:
                env_out[key] = value
            counter += 1

        return env_out
