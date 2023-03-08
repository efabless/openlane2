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
import textwrap
import subprocess
from abc import abstractmethod, ABC
from concurrent.futures import Future
from typing import (
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

from ..state import State
from ..state import DesignFormat, DesignFormatByID
from ..utils import Toolbox
from ..config import Config, Variable
from ..common import (
    mkdirp,
    print,
    rule,
    log,
    slugify,
    warn,
    err,
    final,
    internal,
)

StepConditionLambda = Callable[[Config], bool]


class MissingInputError(ValueError):
    pass


class StepError(ValueError):
    pass


class StepException(StepError):
    pass


class DeferredStepError(StepError):
    pass


REPORT_START_LOCUS = "%OL_CREATE_REPORT"
REPORT_END_LOCUS = "%OL_END_REPORT"

GlobalToolbox = Toolbox(os.path.join(os.getcwd(), "openlane_run", "tmp"))
LastState: State = State()


class Step(ABC):
    """
    An abstract base class for Step objects.

    Steps encapsulate a subroutine that acts upon certain classes of formats
    in an input state and returns a new output state with updated design format
    paths and/or metrics.

    Warning: The initializer for Step is not thread-safe. Please use it on the main
    thread and then, if you're using a Flow object, use `start_step_async`, or
    if you're not, you may use `start` in another thread. That part's fine.

    :param config: A configuration object.

        If running in interactive mode, you can set this to ``None``, where it
        will automatically use :ref:`Config.current_interactive`, but it is
        otherwise required.

    :param state_in: The state object this step will use as an input.

        The state may also be a `Future[State]`, in which case,
        the `run()` call will block until that Future is realized.
        This allows you to chain a number of asynchronous steps.

        If running in interactive mode, you can set this to ``None``, where it
        will use the last generated state, but it is otherwise required.

        See https://en.wikipedia.org/wiki/Futures_and_promises for a primer.

    :param step_dir: A "scratch directory" for the step.

        If not provided, the call stack will be examined for a
        `self.dir_for_step` function, which will then be called to
        get a directory for said step. If not found, a new folder will be
        created in the current working directory.

    :param name: An optional override name for the step. Useful in custom flows.
    :param id: An optional override name for the ID. Useful in custom flows.
    :param long_name: An optional override name for the long name. Useful in custom flows.

        If set to false, Step implementations are expected to
        output nothing to the terminal.
    :param

    :attr flow_control_variable: An optional key for a configuration variable.
        If it exists, if this variable is "False" or "None", the step is skipped.
    :attr flow_control_msg: If `flow_control_variable` causes the step to be
        skipped and this variable is set, the value of this variable is
        printed.
    """

    inputs: List[DesignFormat] = []
    outputs: List[DesignFormat] = []

    id: str = NotImplemented
    name: str
    long_name: str

    flow_control_variable: ClassVar[Optional[str]] = None
    flow_control_msg: ClassVar[Optional[str]] = None
    config_vars: ClassVar[List[Variable]] = []

    start_time: Optional[float] = None
    end_time: Optional[float] = None
    toolbox: Toolbox = GlobalToolbox

    # These are mutable class variables. However, they will only be used
    # when steps are run outside of a Flow, pretty much.
    counter: ClassVar[int] = 1
    # End Mutable Global Variables

    def __init__(
        self,
        config: Optional[Config] = None,
        state_in: Union[Optional[State], Future[State]] = None,
        step_dir: Optional[str] = None,
        id: Optional[str] = None,
        name: Optional[str] = None,
        long_name: Optional[str] = None,
        **kwargs,
    ):
        if self.id == NotImplemented:
            raise NotImplementedError(
                "All subclasses of Step must override the value of id."
            )

        if id is not None:
            self.id = id

        if config is None:
            if current_interactive := Config.current_interactive:
                config = current_interactive
            else:
                raise TypeError("Missing required argument 'config'")

        if state_in is None:
            if config.interactive is not None:
                state_in = LastState
            else:
                raise TypeError("Missing required argument 'state_in'")

        if name is not None:
            self.name = name
        elif not hasattr(self, "name"):
            self.name = self.__class__.__name__

        if long_name is not None:
            self.long_name = long_name
        elif not hasattr(self, "long_name"):
            self.long_name = self.name

        if config.interactive:
            mutable = Config(**kwargs.copy())
            overrides, warnings, errors = Variable.process_config(
                mutable,
                variables=self.config_vars,
            )
            config.update(**overrides)
            for warning in warnings:
                warn(warning)
            if len(errors) != 0:
                err(f"Errors while processing inputs for {self.name}:")
                for error in errors:
                    err(error)
                raise StepException("Failed to handle one or more kwarg variables.")
        elif len(kwargs) != 0:
            raise StepException(
                "Variables may not be passed as keyword arguments unless the Config object is per-step."
            )

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
                    step_dir = os.path.join(
                        os.getcwd(),
                        "openlane_run",
                        f"{Step.counter}-{slugify(self.id)}",
                    )
                    Step.counter += 1
            finally:
                del frame

        self.step_dir = step_dir
        self.config = config.copy()
        self.state_in = state_in

    @classmethod
    def _get_desc(Self) -> str:
        """
        Used for documentation. Use externally at your own peril.
        """
        if hasattr(Self, "long_name"):
            return Self.long_name
        elif hasattr(Self, "name"):
            return Self.name
        return Self.__name__

    @classmethod
    def get_help_md(Self):
        """
        Renders Markdown help for this step to a string.
        """

        result = textwrap.dedent(
            f"""
        ### {Self._get_desc()}

        {Self.__doc__ or ""}

        #### Usage

        <br />

        ```python
        from {Self.__module__} import {Self.__name__}

        # or
        
        from openlane.steps import Step

        Synthesis = Step.get("{Self.id}")
        ``` 

        #### Configuration Variables

        | Variable Name | Type | Description | Default | Units |
        | - | - | - | - | - |
        """
        )
        for var in Self.config_vars:
            units = var.units or ""
            result += f"| `{var.name}` | {var.type_repr_md()} | {var.desc_repr_md()} | `{var.default}` | {units} |\n"

        return result

    @classmethod
    def display_help(Self):
        """
        IPython-only. Displays Markdown help for a given step.
        """
        import IPython.display

        IPython.display.display(IPython.display.Markdown(Self.get_help_md()))

    @final
    def start(
        self,
        toolbox: Optional[Toolbox] = None,
        **kwargs,
    ) -> State:
        """
        Begins execution on a step.

        This method is final and should not be subclassed.

        :param toolbox: The flow's :class:`Toolbox` object, required.

            If not running in a flow, i.e., in interactive mode, you may leave
            this argument as ``None``, where a global toolbox will be used
            instead.

            If running inside a flow, you may also leave this argument as ``None``.
            As a convenience, the call stack will be examined for a :attr:`self.toolbox`,
            which will be used instead.

        :param **kwargs: Passed on to subprocess execution: useful if you want to
            redirect stdin, stdout, etc.

        :returns: An altered State object.
        """
        global LastState

        if toolbox is None:
            try:
                frame = inspect.currentframe()
                if frame is not None:
                    current = frame.f_back
                    while current is not None:
                        locals = current.f_locals
                        if "self" in locals and hasattr(locals["self"], "toolbox"):
                            assert isinstance(locals["self"].toolbox, Toolbox)
                            toolbox = locals["self"].toolbox
                        current = current.f_back
                if toolbox is None:
                    if not self.config.interactive:
                        raise TypeError(
                            "Missing argument 'toolbox' required when not running in a Flow"
                        )
                else:
                    self.toolbox = toolbox
            finally:
                del frame
        else:
            self.toolbox = toolbox

        if isinstance(self.state_in, Future):
            self.state_in = self.state_in.result()

        if self.flow_control_variable is not None:
            flow_control_value = self.config[self.flow_control_variable]
            if isinstance(flow_control_value, bool):
                if not flow_control_value:
                    if self.flow_control_msg is not None:
                        log(self.flow_control_msg)
                    else:
                        log(
                            f"`{self.flow_control_variable}` is set to False: skipping…"
                        )
                        return self.state_in.copy()
            elif flow_control_value is None:
                if self.flow_control_msg is not None:
                    log(self.flow_control_msg)
                else:
                    log(
                        f"Required variable `{self.flow_control_variable}` is set to null: skipping…"
                    )
                return self.state_in.copy()

        mkdirp(self.step_dir)
        with open(os.path.join(self.step_dir, "state_in.json"), "w") as f:
            f.write(self.state_in.dumps())

        self.start_time = time.time()
        rule(f"{self.long_name}")
        self.state_out = self.run(**kwargs)
        self.end_time = time.time()

        with open(os.path.join(self.step_dir, "state_out.json"), "w") as f:
            f.write(self.state_out.dumps())

        if self.config.interactive:
            LastState = self.state_out
        return self.state_out

    @internal
    @abstractmethod
    def run(self, **kwargs) -> State:
        """
        The "core" of a step.

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

    def get_log_path(self) -> str:
        return os.path.join(self.step_dir, f"{slugify(self.id)}.log")

    @internal
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
        :param log_to: An optional override for the log path from `get_log_path`.
            Useful for if you run multiple subprocesses within one step.
        :param **kwargs: Passed on to subprocess execution: useful if you want to
            redirect stdin, stdout, etc.
        :raises subprocess.CalledProcessError: If the process has a non-zero exit,
            this exception will be raised.
        """
        log_path = log_to or self.get_log_path()
        log_file = open(log_path, "w")
        cmd_str = [str(arg) for arg in cmd]

        with open(os.path.join(self.step_dir, "COMMANDS"), "a+") as f:
            f.write(" ".join(cmd_str))
            f.write("\n")

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
                    print(line.strip())
                    log_file.write(line)
        returncode = process.wait()
        if returncode != 0:
            raise subprocess.CalledProcessError(returncode, process.args)

    @internal
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
        def register(Self) -> Callable[[Type[Step]], Type[Step]]:
            """
            Adds a step type to the registry using its :mem:`Step.id` attribute.
            """

            def decorator(cls: Type[Step]) -> Type[Step]:
                Self._registry[cls.id] = cls
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
    get = StepFactory.get

    def layout_preview(self) -> Optional[str]:
        """
        Returns an HTML tag that could act as a preview for a specific stage.
        """
        return None

    def _repr_markdown_(self) -> str:
        if self.state_out is None:
            return """
                ### Step not yet executed.
            """
        assert isinstance(self.state_in, State)
        assert self.start_time is not None and self.end_time is not None

        result = ""
        time_elapsed = self.end_time - self.start_time

        result += f"#### Time Elapsed: {'%.2f' % time_elapsed}s\n"

        views_updated = []
        for id, value in dict(self.state_out).items():
            assert isinstance(id, str)
            if value is None:
                continue

            if self.state_in.get(id) != value:
                views_updated.append(DesignFormatByID[id].value[2])

        if len(views_updated):
            result += "#### Views updated:\n"
            for view in views_updated:
                result += f"* {view}\n"

        if preview := self.layout_preview():
            result += "#### Preview:\n"
            result += preview

        return result

    def display_result(self):
        """
        IPython-only. Displays the results of a given step.
        """
        import IPython.display

        IPython.display.display(IPython.display.Markdown(self._repr_markdown_()))
