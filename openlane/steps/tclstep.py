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
from enum import Enum
from decimal import Decimal
from typing import List

from .step import Step
from .state import State
from ..common import get_script_dir


class TclStep(Step):
    """
    A subclass of `Step` that primarily deals with running Tcl-based utilities,
    such as Yosys, OpenROAD and Magic.

    A TclStep Step corresponds to running one Tcl script with such a utility.
    """

    def get_script_path(self):
        """
        :returns: A Tcl script to be run by this step.
        """
        return os.path.join(get_script_dir(), "tclsh", "hello.tcl")

    def get_command(self) -> List[str]:
        """
        :returns: The command used to run the script.
        """
        return ["tclsh", self.get_script_path()]

    def run(
        self,
        **kwargs,
    ) -> State:
        """
        This overriden `run()` function prepares configuration variables and
        inputs for use with Tcl: specifically, it converts them all to
        environment variables so they may be used by the Tcl scripts being called.

        Additionally, it logs the output to a `.log` file named after the script.

        When overriding in a subclass, you may find it useful to use this pattern:

        ```
            kwargs, env = self.extract_env(kwargs)
            env["CUSTOM_ENV_VARIABLE"] = "1"
            return super().run(env=env, **kwargs)
        ```

        This will allow you to add further custom environment variables to a call
        while still respecting an `env` argument further up the call-stack.


        :param **kwargs: Passed on to subprocess execution: useful if you want to
            redirect stdin, stdout, etc.
        """
        state = super().run()
        command = self.get_command()
        script = self.get_script_path()

        kwargs, env = self.extract_env(kwargs)

        env["SCRIPTS_DIR"] = get_script_dir()
        env["STEP_DIR"] = os.path.abspath(self.step_dir)

        for element in self.config.keys():
            value = self.config[element]
            if value is None:
                continue

            if isinstance(value, list):
                value = " ".join(list(map(lambda x: str(x), value)))
            elif isinstance(value, Enum):
                value = value._name_
            elif isinstance(value, bool):
                value = "1" if value else "0"
            elif isinstance(value, Decimal) or isinstance(value, int):
                value = str(value)

            env[element] = value

        for input in self.inputs:
            env[f"CURRENT_{input.name}"] = state[input]

        for output in self.outputs:
            filename = f"{self.config['DESIGN_NAME']}.{output.value[1]}"
            env[f"SAVE_{output.name}"] = os.path.join(self.step_dir, filename)

        log_filename = os.path.splitext(os.path.basename(script))[0]
        log_path = os.path.join(self.step_dir, f"{log_filename}.log")

        self.run_subprocess(
            command,
            env=env,
            log_to=log_path,
            **kwargs,
        )

        for output in self.outputs:
            state[output] = env[f"SAVE_{output.name}"]

        return state
