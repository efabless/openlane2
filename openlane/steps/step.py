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
import time
import inspect
import subprocess
from abc import abstractmethod, ABC
from concurrent.futures import Future
from typing import (
    final,
    List,
    Callable,
    Optional,
    Union,
    Tuple,
    Sequence,
    Dict,
    ClassVar,
    Type,
)

import slugify

from .state import State
from ..utils import Toolbox
from ..config import Config
from .design_format import DesignFormat
from ..common import mkdirp, console, err, rule, log

StepConditionLambda = Callable[[Config], bool]


class MissingInputError(ValueError):
    pass


REPORT_START_LOCUS = "%OL_CREATE_REPORT"
REPORT_END_LOCUS = "%OL_END_REPORT"


class Step(ABC):
    """
    An abstract base class for Step objects.

    Steps encapsulate a subroutine that acts upon certain classes of formats
    in an input state and returns a new output state with updated design format
    paths and/or metrics.

    Properties:

        `inputs`: A list of design formats used by the step as an input.
        `outputs`: A list of design formats that are output by this step.

        `name`: A short name for the step, used primarily in the progress bar
            of sequential flows.

            If not set by a subclass, the Python name of the Step class is used.
        `id`: A valid filesystem name for the step, user primarily in step
            directories.

            If not set by a subclass, `.name` is passed through `slugify` and
            used as an ID.

        `long_name`:  A verbose and descriptive name for the step,
            used to separate logs in the terminal.

            If not set by a subclass, `.name` is used.

        `flow_control_variable`: An optional key for a boolean configuration variable.

            If it exists, if this variable is configured to be false,
            the Step is skipped.
    """

    inputs: List[DesignFormat] = []
    outputs: List[DesignFormat] = []

    id: str
    name: str
    long_name: str

    flow_control_variable: ClassVar[Optional[str]] = None

    def __init__(
        self,
        config: Optional[Config] = None,
        state_in: Union[Optional[State], Future[State]] = None,
        step_dir: Optional[str] = None,
        id: Optional[str] = None,
        name: Optional[str] = None,
        long_name: Optional[str] = None,
        silent: bool = False,
    ):
        """
        Warning: This initializer is not thread-safe. Please use it on the main
        thread and then, if you're using a Flow object, use `run_step_async`, or
        if you're not, you may use `start` in another thread. That part's fine.

        :param config: A configuration object.
            If not provided, as a convenience, the call stack will be
            examined for a `self.config`, and the first one encountered
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

        :param name: An optional override name for the step. Useful in custom flows.
        :param id: An optional override name for the ID. Useful in custom flows.
        :param long_name: An optional override name for the long name. Useful in custom flows.

        :param silent: A variable stating whether a step should output to the
        terminal.

            If set to false, Step implementations are expected to
            output nothing to the terminal.
        """
        if name is not None:
            self.name = name
        elif not hasattr(self, "name"):
            self.name = self.__class__.__name__

        if id is not None:
            self.id = id
        elif not hasattr(self, "id"):
            self.id = slugify.slugify(self.name)

        if long_name is not None:
            self.long_name = long_name
        elif not hasattr(self, "long_name"):
            self.long_name = self.name

        if config is None:
            try:
                frame = inspect.currentframe()
                if frame is not None:
                    current = frame.f_back
                    while current is not None:
                        locals = current.f_locals
                        if "self" in locals and hasattr(locals["self"], "config"):
                            config = locals["self"].config.copy()
                        current = current.f_back
                if config is None:
                    raise TypeError("Missing required argument 'config'")
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
                    raise TypeError("Missing required argument 'state_in'")
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
                    raise TypeError("Missing required argument 'step_dir'")
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

        if isinstance(self.state_in, Future):
            self.state_in = self.state_in.result()

        if self.flow_control_variable is not None:
            flow_control_value = self.config[self.flow_control_variable]
            if not flow_control_value:
                log(f"`{self.flow_control_variable}` is set to false: skipping…")
                return self.state_in.copy()

        mkdirp(self.step_dir)
        with open(os.path.join(self.step_dir, "state_in.json"), "w") as f:
            f.write(self.state_in.dumps())

        self.start_time = time.time()
        if not self.silent:
            rule(f"{self.long_name}")
        self.state_out = self.run(**kwargs)
        self.end_time = time.time()

        with open(os.path.join(self.step_dir, "state_out.json"), "w") as f:
            f.write(self.state_out.dumps())

        return self.state_out

    @abstractmethod
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

        assert isinstance(self.state_in, State)

        for input in self.inputs:
            value = self.state_in.get(input)
            if value is None:
                raise MissingInputError(
                    f"{type(self).__name__}: missing required input '{input.name}'"
                )

        return self.state_in.copy()

    def run_subprocess(
        self,
        cmd: Sequence[Union[str, os.PathLike]],
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

        cmd_str = [str(arg) for arg in cmd]

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
            err("Command failed: ", _stack_offset=4)
            console.print("\t", " ".join(cmd_str))
            raise subprocess.CalledProcessError(returncode, process.args)

    def extract_env(self, kwargs) -> Tuple[dict, Dict[str, str]]:
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

    class StepFactory(object):
        """
        A factory singleton for Steps, allowing steps types to be registered and then
        retrieved by name.

        See https://en.wikipedia.org/wiki/Factory_(object-oriented_programming) for
        a primer.
        """

        _registry: ClassVar[Dict[str, Type[Step]]] = {}

        @classmethod
        def register(Self, registered_name: str) -> Callable[[Type[Step]], Type[Step]]:
            """
            Adds a step type to the registry.

            :param flow: A Step **type** (not object)
            """

            def decorator(cls: Type[Step]) -> Type[Step]:
                Self._registry[registered_name] = cls
                return cls

            return decorator

        @classmethod
        def get(Self, name: str) -> Optional[Type[Step]]:
            """
            Retrieves a Step type from the registry using a lookup string.

            :param name: The registered name of the Step. Case-sensitive.
            """
            return Self._registry.get(name)

        @classmethod
        def list(Self) -> List[str]:
            """
            :returns: A list of strings representing Python names of all registered
            steps.
            """
            return list(Self._registry.keys())

    factory = StepFactory
