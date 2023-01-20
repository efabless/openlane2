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
import time
import subprocess
from enum import Enum
from io import TextIOWrapper
from typing import List, Callable, Optional, final

from .state import State, DesignFormat, Output
from ..config import Config
from ..common import mkdirp, console, error

StepConditionLambda = Callable[[Config], bool]


def get_script_dir():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scripts",
    )


class MissingInputError(ValueError):
    pass


REPORT_START_LOCUS = "%OL_CREATE_REPORT"
REPORT_END_LOCUS = "%OL_END_REPORT"

invalid_for_path = re.compile(r"[^\w_-]+")


class Step(object):
    """
    Default Step Object

    Does nothing.
    """

    inputs: List[DesignFormat] = []
    outputs: List[Output] = []
    name: Optional[str] = None
    long_name: Optional[str] = None

    def get_name(self):
        return self.name or self.__class__.__name__

    def get_name_escaped(self):
        return invalid_for_path.sub("_", self.get_name()).lower()

    def get_long_name(self):
        return self.long_name or self.get_name()

    def __init__(
        self,
        config: Config,
        state_in: State,
        run_dir: str,
        prefix: Optional[str] = None,
        name: Optional[str] = None,
        silent: bool = False,
    ):
        if name is not None:
            self.name = name

        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.step_dir = os.path.join(
            run_dir, f"{prefix or ''}{self.get_name_escaped()}"
        )
        self.config = config.copy()
        self.state_in = state_in
        self.silent = silent

    @final
    def start(
        self,
        **kwargs,
    ) -> State:
        self.start_time = time.time()
        if not self.silent:
            console.rule(f"{self.get_long_name()}")
        mkdirp(self.step_dir)
        self.state_out = self.run(**kwargs)
        self.end_time = time.time()
        return self.state_out

    def run(self, **kwargs) -> State:
        """
        When subclassing, override this function, then call it first thing
        via super().run(**kwargs). This lets you use the input verification and
        the copying code.
        """
        for input in self.inputs:
            value = self.state_in.get(input.name)
            if value is None:
                raise MissingInputError(
                    f"{type(self).__name__}: missing required input '{input.name}'"
                )

        return self.state_in.copy()

    @final
    def run_subprocess(
        self,
        cmd,
        log_to: Optional[str] = None,
        step_dir: Optional[str] = None,
        **kwargs,
    ):
        log_file = open(os.devnull, "w")
        if log_to is not None:
            log_file.close()
            log_file = open(log_to, "w")

        kwargs = kwargs.copy()
        process = subprocess.Popen(
            cmd,
            encoding="utf8",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            **kwargs,
        )
        process_stdout: TextIOWrapper = process.stdout  # type: ignore
        current_rpt = None
        while line := process_stdout.readline():
            if step_dir is not None and line.startswith(REPORT_START_LOCUS):
                report_name = line[len(REPORT_START_LOCUS) + 1 :].strip()
                report_path = os.path.join(step_dir, report_name)
                current_rpt = open(report_path, "w")
            elif line.startswith(REPORT_END_LOCUS):
                if current_rpt is not None:
                    current_rpt.close()
                current_rpt = None
            elif current_rpt is not None:
                current_rpt.write(line)
            else:
                if not self.silent:
                    console.print(line.strip())
                log_file.write(line)
        returncode = process.wait()
        if returncode != 0:
            error(f"Command '{' '.join(cmd)}' failed.", _stack_offset=3)
            raise subprocess.CalledProcessError(returncode, process.args)


class TclStep(Step):
    def run(
        self,
        **kwargs,
    ) -> State:
        state = super().run()
        command = self.get_command()
        script = self.get_script_path()

        env = kwargs.get("env")
        if env is None:
            env = os.environ.copy()
        else:
            kwargs = kwargs.copy()
            del kwargs["env"]

        env["SCRIPTS_DIR"] = get_script_dir()
        env["STEP_DIR"] = self.step_dir
        for element in self.config.keys():
            value = self.config[element]
            if value is None:
                continue
            if isinstance(value, list):
                value = " ".join(list(map(lambda x: str(x), value)))
            elif isinstance(value, Enum):
                value = value._name_
            else:
                value = str(value)
            env[element] = value

        for input in self.inputs:
            env[f"CURRENT_{input.name}"] = state[input.name]

        for output in self.outputs:
            filename = f"{self.config['DESIGN_NAME']}.{output.format.value[0]}"
            env[f"SAVE_{output.format.name}"] = os.path.join(self.step_dir, filename)

        log_filename = os.path.splitext(os.path.basename(script))[0]
        log_path = os.path.join(self.step_dir, f"{log_filename}.log")

        self.run_subprocess(
            command,
            env=env,
            log_to=log_path,
            step_dir=self.step_dir,
            **kwargs,
        )

        for output in self.outputs:
            if not output.update:
                continue
            state[output.format.name] = env[f"SAVE_{output.format.name}"]

        return state

    def get_script_path(self):
        return os.path.join(get_script_dir(), "tclsh", "hello.tcl")

    def get_command(self) -> List[str]:
        return ["tclsh", self.get_script_path()]
