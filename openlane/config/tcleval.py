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
import tkinter
import tempfile
from decimal import Decimal, InvalidOperation

from .config import Config


def env_from_tcl(env_in: Config, tcl_in_path: str) -> Config:
    tcl_in = open(tcl_in_path).read()
    interpreter = tkinter.Tcl()

    initial_env = os.environ.copy()
    env_out = Config(env_in)

    with tempfile.NamedTemporaryFile("r+") as f:
        env_str = ""
        for key, value in env_in.items():
            env_str += f"set ::env({key}) {{{value}}}\n"
        tcl_script = f"""
        {env_str}
        {tcl_in}
        set f [open {f.name} WRONLY]
        foreach key [array names ::env] {{
            puts $f "$key $::env($key)\\0"
        }}
        close $f
        """

        interpreter.eval(tcl_script)

        f.seek(0)
        env_strings = f.read()

        for line in env_strings.split("\0\n"):
            if line.strip() == "":
                continue
            key, value = line.split(" ", 1)
            try:
                value = Decimal(value)
            except InvalidOperation:
                pass
            if initial_env.get(key) is None:
                env_out[key] = value

    return env_out
