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
import re
import tkinter
import tempfile
from typing import Dict, Mapping, Any

setter_rx = re.compile(r"set\s+(?:\:\:)?env\(\s*(\w+)\s*\)")


def env_from_tcl(env_in: Mapping[str, Any], tcl_in: str) -> Dict[str, Any]:
    interpreter = tkinter.Tcl()
    env_out = dict(env_in)
    keys_modified = setter_rx.findall(tcl_in)
    with tempfile.NamedTemporaryFile("r+") as f:
        env_str = ""
        unset_env_str = ""
        for key, value in env_in.items():
            env_str += f"set ::env({key}) {{{value}}}\n"
            unset_env_str += f"unset ::env({key})\n"

        tcl_script = f"""
        {env_str}
        {tcl_in}
        set f [open {f.name} WRONLY]
        foreach key [array names ::env] {{
            puts $f "$key $::env($key)\\0"
        }}
        close $f
        {unset_env_str}
        """
        interpreter.eval(tcl_script)

        f.seek(0)
        env_strings = f.read()

        for line in env_strings.split("\0\n"):
            if line.strip() == "":
                continue
            key, value = line.split(" ", 1)
            if key in keys_modified:
                env_out[key] = value

    return env_out
