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
import re
import time
import inspect
import subprocess
from enum import Enum
from decimal import Decimal
from concurrent.futures import Future
from typing import final, List, Callable, Optional, Union, Tuple

from .state import State, DesignFormat, Output
from ..config import Config
from ..common import mkdirp, console, err, rule
from ..utils import Toolbox

StepConditionLambda = Callable[[Config], bool]


def get_script_dir():
    """
    Gets the OpenLane tool `scripts` directory.

    This implementation is jank and should be redone.
    """
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
    The base Step class from which all other Step class inherit.

    If used in a flow, this particular Step does... absolutely nothing.
    """

    inputs: List[DesignFormat] = []
    outputs: List[Union[DesignFormat, Output]] = []

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
        config: Optional[Config] = None,
        state_in: Union[Optional[State], Future[State]] = None,
        step_dir: Optional[str] = None,
        name: Optional[str] = None,
        silent: bool = False,
    ):
        """
        :param config: A configuration object.
            If not provided, as a convenience, the call stack will be
            examined for a `self.config_in`, and the first one encountered
            will be used.

        :param state_in: The state object this step will use as an input.

            If not provided, the call stack will be examined for a
            `state_list`, and the latest one will be used as an input state.

            The state may also be a `Future[State]`, in which case,
            the `run()` call will block until that Future is realized.
            This allows you to chain a number of asynchronous steps.

            See https://en.wikipedia.org/wiki/Futures_and_promises for a primer.

        :param step_dir: A "scratch directory" for the step.

            If not provided, the call stack will be examined for a
            `self.dir_for_step` function, which will then be called to
            get a directory for said step.

        :param name: An optional string name for the step. Useful in custom flows.

        :param silent: A variable stating whether a step should output to the
        terminal.

            If set to false, Step implementations are expected to
            output nothing to the terminal.
        """
        if name is not None:
            self.name = name

        if config is None:
            try:
                frame = inspect.currentframe()
                if frame is not None:
                    current = frame.f_back
                    while current is not None:
                        locals = current.f_locals
                        if "self" in locals and hasattr(locals["self"], "config_in"):
                            config = locals["self"].config_in.copy()
                        current = current.f_back
                if config is None:
                    raise Exception("")
            finally:
                del frame

        if state_in is None:
            try:
                frame = inspect.currentframe()
                if frame is not None:
                    current = frame.f_back
                    while current is not None:
                        locals = current.f_locals
                        if "state_list" in locals:
                            state_list = locals["state_list"]
                            state_in = state_list[-1]
                        current = current.f_back
                if state_in is None:
                    raise Exception("")
            finally:
                del frame

        if step_dir is None:
            try:
                frame = inspect.currentframe()
                if frame is not None:
                    current = frame.f_back
                    while current is not None:
                        locals = current.f_locals
                        if "self" in locals and hasattr(locals["self"], "dir_for_step"):
                            step_dir = locals["self"].dir_for_step(self)
                        current = current.f_back
                if step_dir is None:
                    raise Exception("")
            finally:
                del frame

        self.toolbox = Toolbox(os.path.join(step_dir, "tmp"))

        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.step_dir = step_dir
        self.config = config.copy()
        self.state_in = state_in
        self.silent = silent

    @final
    def start(
        self,
        toolbox: Optional[Toolbox] = None,
        **kwargs,
    ) -> State:
        """
        Begins execution on a step. This is the function that should be used
        by flows- `run()` is considered private and may only be called by `Step`
        and its subclasses.

        `start()` is final and should not be subclassed.

        :param toolbox: A `Toolbox` object initialized with a temporary directory
            fit for the flow in question.

            If not provided, as a convenience, the call stack will be
            examined for a `self.toolbox`, which will be used instead.
            What this means is that when inside of a Flow: you can just call
            `step.start()` and not worry about this.

            If said toolbox doesn't exist, the step will begrudingly create
            one that uses its own step directory, however this will cause
            cached functions inside the toolbox, i.e., those that perform
            common file processing functions in the flow (trimming
            liberty files, etc.) to not cache their results across steps.

        :param **kwargs: Passed on to subprocess execution: useful if you want to
            redirect stdin, stdout, etc.

        :returns: An altered State object.
        """
        if toolbox is None:
            try:
                frame = inspect.currentframe()
                if frame is not None:
                    current = frame.f_back
                    while current is not None:
                        locals = current.f_locals
                        if "self" in locals and hasattr(locals["self"], "toolbox"):
                            assert isinstance(locals["self"].toolbox, Toolbox)
                            self.toolbox = locals["self"].toolbox
                        current = current.f_back
            finally:
                del frame

        self.start_time = time.time()
        if not self.silent:
            rule(f"{self.get_long_name()}")
        mkdirp(self.step_dir)
        self.state_out = self.run(**kwargs)
        self.end_time = time.time()
        return self.state_out

    def run(self, **kwargs) -> State:
        """
        The "core" of a step. **You should not be calling this function outside
        of `Step` or its subclasses.**

        When subclassing, override this function, then call it first thing
        via super().run(**kwargs). This lets you use the input verification and
        the State copying code, as well as resolving the `state_in` if `state_in`
        is a future.

        :param **kwargs: Passed on to subprocess execution: useful if you want to
            redirect stdin, stdout, etc.
        """
        if isinstance(self.state_in, Future):
            self.state_in = self.state_in.result()

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
        cmd: List[str],
        log_to: Optional[str] = None,
        **kwargs,
    ):
        """
        A helper function for `Step` objects to run subprocesses.

        The output from the subprocess is processed line-by-line.

        :param cmd: A list of variables, representing a program and its arguments,
            similar to how you would use it in a shell.
        :param log_to: An optional path to log all output from the subprocess to.
        :param **kwargs: Passed on to subprocess execution: useful if you want to
            redirect stdin, stdout, etc.
        :raises subprocess.CalledProcessError: If the process has a non-zero exit,
            this exception will be raised.
        """
        log_file = open(os.devnull, "w")
        if log_to is not None:
            log_file.close()
            log_file = open(log_to, "w")

        kwargs = kwargs.copy()
        if "stdin" not in kwargs:
            kwargs["stdin"] = open(os.devnull, "r")
        if "stdout" not in kwargs:
            kwargs["stdout"] = subprocess.PIPE
        if "stderr" not in kwargs:
            kwargs["stderr"] = subprocess.STDOUT
        process = subprocess.Popen(
            cmd,
            encoding="utf8",
            **kwargs,
        )
        if process_stdout := process.stdout:
            current_rpt = None
            while line := process_stdout.readline():
                if self.step_dir is not None and line.startswith(REPORT_START_LOCUS):
                    report_name = line[len(REPORT_START_LOCUS) + 1 :].strip()
                    report_path = os.path.join(self.step_dir, report_name)
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
            err(f"Command '{' '.join(cmd)}' failed.", _stack_offset=3)
            raise subprocess.CalledProcessError(returncode, process.args)

    def extract_env(self, kwargs) -> Tuple[dict, dict]:
        """
        An assisting function: Given a `kwargs` object, it does the following:

            * If the kwargs object has an "env" variable, it separates it into
                its own variable.
            * If the kwargs object has no "env" variable, a new "env" dictionary
                is created based on the current environment.

        :param kwargs: A Python keyword arguments object.
        :returns (kwargs, env): A kwargs without an `env` object, and an isolated `env` object.
        """
        env = kwargs.get("env")
        if env is None:
            env = os.environ.copy()
        else:
            kwargs = kwargs.copy()
            del kwargs["env"]
        return (kwargs, env)


class TclStep(Step):
    """
    A subclass of `Step` that primarily deals with running Tcl-based utilities,
    such as Yosys, OpenROAD and Magic.

    A TclStep script corresponds to running one Tcl script with such a utility.
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
        env["STEP_DIR"] = self.step_dir

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
            env[f"CURRENT_{input.name}"] = state[input.name]

        for output in self.outputs:
            filename = f"{self.config['DESIGN_NAME']}.{output.value[0]}"
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
            if isinstance(output, Output) and not output.update:
                continue
            state[output.name] = env[f"SAVE_{output.name}"]

        return state
