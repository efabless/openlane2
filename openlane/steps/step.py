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
import textwrap
import subprocess
from itertools import zip_longest
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

from ..state import State, InvalidState
from ..state import DesignFormat
from ..utils import Toolbox
from ..config import Config, Variable
from ..common import (
    mkdirp,
    slugify,
    final,
    internal,
)
from ..logging import (
    rule,
    verbose,
    info,
    warn,
    err,
)


class StepError(ValueError):
    pass


class DeferredStepError(StepError):
    pass


class StepException(StepError):
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
    thread and then, if you're using a Flow object, use ``start_step_async``, or
    if you're not, you may use ``start`` in another thread. That part's fine.

    :param config: A configuration object.

        If running in interactive mode, you can set this to ``None``, but it is
        otherwise required.

    :param flow: The parent flow, if applicable.

    :param state_in: The state object this step will use as an input.

        The state may also be a ``Future[State]``, in which case,
        the ``start()`` call will block until that Future is realized.
        This allows you to chain a number of asynchronous steps.

        See https://en.wikipedia.org/wiki/Futures_and_promises for a primer.

        If running in interactive mode, you can set this to ``None``, where it
        will use the last generated state, but it is otherwise required.

    :param step_dir: A "scratch directory" for the step. Required.

        You may omit this argument as ``None`` if "flow" is specified.

    :param id: A string ID for the Step. The convention is f"{a}.{b}", where the
        first is common between all Steps using the same tools.

        The ID should be in ``UpperCamelCase``.

        While this is technically an instance variable, it is expected for every
        subclass to override this variable and instances are only to change it
        to disambiguate when the same step is used multiple times in a flow.

    :param name: A short name for the Step, used in progress bars and
        the like.

        While this is technically an instance variable, it is expected for every
        subclass to override this variable and instances are only to change it
        to disambiguate when the same step is used multiple times in a flow.

    :param long_name: A longer descriptive for the Step, used to delimit
        logs.

        While this is technically an instance variable, it is expected for every
        subclass to override this variable and instances are only to change it
        to disambiguate when the same step is used multiple times in a flow.

    :cvar inputs: A list of :class:`openlane.state.DesignFormat` objects that
        are required for this step. These will be validated by the :meth:`start`
        method.

    :cvar outputs: A list of :class:`openlane.state.DesignFormat` objects that
        may be emitted by this step. A step is not allowed to modify design
        formats not declared in ``outputs``.

    :cvar flow_control_variable: An optional key for a configuration variable.

        If running inside a Flow, and this exists, if this variable is "False"
        or "None", the step is skipped.

    :cvar flow_control_msg: If ``flow_control_variable`` causes the step to be
        skipped and this variable is set, the value of this variable is
        printed.

    :cvar config_vars: A list of configuration :class:`openlane.config.Variable` objects
        to be used to alter the behavior of this Step.
    """

    class _FlowType(ABC):
        """
        "Forward declaration" for the methods a step uses to interact with its
        parent Flow.
        """

        toolbox: Optional[Toolbox] = None

        @abstractmethod
        def dir_for_step(self, step: Step) -> str:
            pass

    id: str = NotImplemented
    name: str
    long_name: str

    inputs: ClassVar[List[DesignFormat]] = []
    outputs: ClassVar[List[DesignFormat]] = []
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
        flow: Optional[_FlowType] = None,
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
            config = config.copy(**overrides)
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

        self.config = config.copy()

        self.flow = flow
        if step_dir is None:
            if self.flow is not None:
                self.step_dir = self.flow.dir_for_step(self)
            elif not self.config.interactive:
                raise TypeError("Missing required argument 'step_dir'")
            else:
                self.step_dir = os.path.join(
                    os.getcwd(),
                    "openlane_run",
                    f"{Step.counter}-{slugify(self.id)}",
                )
                Step.counter += 1
        else:
            self.step_dir = step_dir

        state_in_future: Future[State] = Future()
        if isinstance(state_in, State):
            state_in_future.set_result(state_in)
        else:
            state_in_future = state_in
        self.state_in = state_in_future

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
    def get_help_md(Self, docstring_override: str = ""):
        """
        Renders Markdown help for this step to a string.
        """
        doc_string = docstring_override
        if Self.__doc__:
            doc_string = textwrap.dedent(Self.__doc__)

        result = (
            textwrap.dedent(
                f"""\
                ### <a name="{Self.id}"></a> {Self._get_desc()}

                ```{{eval-rst}}
                %s
                ```

                #### Importing

                ```python
                from {Self.__module__} import {Self.__name__}

                # or
                
                from openlane.steps import Step

                {Self.__name__} = Step.get("{Self.id}")
                ```
                """
            )
            % doc_string
        )
        if len(Self.inputs) + len(Self.outputs):
            result += textwrap.dedent(
                """
                #### Inputs and Outputs

                | Inputs | Outputs |
                | - | - |
                """
            )
            for input, output in zip_longest(Self.inputs, Self.outputs):
                input_str = ""
                if input is not None:
                    input_str = f"{input.value.name} (.{input.value.extension})"

                output_str = ""
                if output is not None:
                    if not isinstance(output, DesignFormat):
                        raise StepException(
                            f"Output '{output}' is not a valid DesignFormat enum object."
                        )
                    output_str = f"{output.value.name} (.{output.value.extension})"
                result += f"| {input_str} | {output_str} |"

        if len(Self.config_vars):
            result += textwrap.dedent(
                """
                #### Configuration Variables

                | Variable Name | Type | Description | Default | Units |
                | - | - | - | - | - |
                """
            )
            for var in Self.config_vars:
                units = var.units or ""
                result += f'| <a name="{Self.id}.{var.name}"></a>`{var.name}` | {var.type_repr_md()} | {var.desc_repr_md()} | `{var.default}` | {units} |\n'

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

            If running in interactive mode, you may omit this argument as ``None``,
            where a global toolbox will be used instead.

            If running inside a flow, you may also omit this argument as ``None``,
            where the flow's toolbox will used to be instead.

        :param **kwargs: Passed on to subprocess execution: useful if you want to
            redirect stdin, stdout, etc.

        :returns: An altered State object.
        """
        global LastState

        if toolbox is None:
            if self.flow is not None:
                if toolbox := self.flow.toolbox:
                    self.toolbox = toolbox
                else:
                    raise StepException(
                        "Attempted to 'start' a step before its parent Flow."
                    )
            elif not self.config.interactive:
                raise TypeError(
                    "Missing argument 'toolbox' required when not running in a Flow"
                )
            else:
                # Use the default global value.
                pass
        else:
            self.toolbox = toolbox

        state_in_result = self.state_in.result()

        rule(f"{self.long_name}")

        if self.flow is not None and self.flow_control_variable is not None:
            flow_control_value = self.config[self.flow_control_variable]
            if isinstance(flow_control_value, bool):
                if not flow_control_value:
                    if self.flow_control_msg is not None:
                        info(self.flow_control_msg)
                    else:
                        info(
                            f"`{self.flow_control_variable}` is set to False: skipping {self.id} …"
                        )
                        return state_in_result.copy()
            elif flow_control_value is None:
                if self.flow_control_msg is not None:
                    info(self.flow_control_msg)
                else:
                    info(
                        f"Required variable '{self.flow_control_variable}' is set to null: skipping…"
                    )
                return state_in_result.copy()

        mkdirp(self.step_dir)
        with open(os.path.join(self.step_dir, "state_in.json"), "w") as f:
            f.write(state_in_result.dumps())

        self.start_time = time.time()
        self.state_out = self.run(state_in_result, **kwargs)
        try:
            self.state_out.validate()
        except InvalidState as e:
            raise StepException(f"Step {self.name} generated invalid state: {e}")
        self.end_time = time.time()

        with open(os.path.join(self.step_dir, "state_out.json"), "w") as f:
            f.write(self.state_out.dumps())

        if self.config.interactive:
            LastState = self.state_out
        return self.state_out

    @abstractmethod
    def run(self, state_in: State, **kwargs) -> State:
        """
        The "core" of a step.

        When subclassing, override this function. You may call it first thing
        via super().run(**kwargs) where it verifies the existence of inputs and
        copies the input state.
        This step is considered per-object private, i.e., if a Step's run is
        called anywhere outside of the same object's :meth:`start`, its behavior
        is undefined.

        :param state_in: The input state.

            Note that `self.state_in` is stored as a future and would need to be
            resolved before use first otherwise.

            For reference, `start()` is responsible for resolving it
            for `.run()`.
        :param **kwargs: Passed on to subprocess execution: useful if you want to
            redirect stdin, stdout, etc.
        """

        for input in self.inputs:
            value = state_in[input]
            if value is None:
                raise StepException(
                    f"{type(self).__name__}: missing required input '{input.name}'"
                )

        return state_in.copy()

    def get_log_path(self) -> str:
        return os.path.join(self.step_dir, f"{slugify(self.id)}.log")

    @internal
    def run_subprocess(
        self,
        cmd: Sequence[Union[str, os.PathLike]],
        log_to: Optional[str] = None,
        silent: bool = False,
        **kwargs,
    ):
        """
        A helper function for :class:`Step` objects to run subprocesses.

        The output from the subprocess is processed line-by-line.

        :param cmd: A list of variables, representing a program and its arguments,
            similar to how you would use it in a shell.
        :param log_to: An optional override for the log path from ``get_log_path``.
            Useful for if you run multiple subprocesses within one step.
        :param silent: If specified, the subprocess does not print anything to
            the terminal. Useful when running multiple processes simultaneously.
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
            cmd_str,
            encoding="utf8",
            **kwargs,
        )
        lines = ""
        if process_stdout := process.stdout:
            current_rpt = None
            while line := process_stdout.readline():
                lines += line
                if self.step_dir is not None and line.startswith(REPORT_START_LOCUS):
                    report_name = line[len(REPORT_START_LOCUS) + 1 :].strip()
                    report_path = os.path.join(self.step_dir, report_name)
                    report_dir = os.path.dirname(report_path)
                    mkdirp(report_dir)
                    current_rpt = open(report_path, "w")
                elif line.startswith(REPORT_END_LOCUS):
                    if current_rpt is not None:
                        current_rpt.close()
                    current_rpt = None
                elif current_rpt is not None:
                    log_file.write(line)
                    current_rpt.write(line)
                    # No echo- the timing reports especially can be very large
                    # and terminal emulators will slow the flow down.
                else:
                    log_file.write(line)
                    # hack for sky130 ff libraries
                    if "table template" in line:
                        continue
                    if not silent:
                        verbose(line.strip())
        returncode = process.wait()
        split_lines = lines.split("\n")
        if returncode != 0:
            err("\n".join(split_lines[-10:]))
            err(f"Log file: {log_path}")
            raise subprocess.CalledProcessError(returncode, process.args)

    @internal
    def extract_env(self, kwargs) -> Tuple[dict, Dict[str, str]]:
        """
        An assisting function: Given a ``kwargs`` object, it does the following:

            * If the kwargs object has an "env" variable, it separates it into
                its own variable.
            * If the kwargs object has no "env" variable, a new "env" dictionary
                is created based on the current environment.

        :param kwargs: A Python keyword arguments object.
        :returns (kwargs, env): A kwargs without an ``env`` object, and an isolated ``env`` object.
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
            Adds a step type to the registry using its :attr:`Step.id` attribute.
            """

            def decorator(cls: Type[Step]) -> Type[Step]:
                Self._registry[cls.id.lower()] = cls
                return cls

            return decorator

        @classmethod
        def get(Self, name: str) -> Optional[Type[Step]]:
            """
            Retrieves a Step type from the registry using a lookup string.

            :param name: The registered name of the Step. Case-insensitive.
            """
            return Self._registry.get(name.lower())

        @classmethod
        def list(Self) -> List[str]:
            """
            :returns: A list of IDs of all registered names.
            """
            return [cls.id for cls in Self._registry.values()]

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
        state_in = self.state_in.result()
        assert self.start_time is not None and self.end_time is not None

        result = ""
        time_elapsed = self.end_time - self.start_time

        result += f"#### Time Elapsed: {'%.2f' % time_elapsed}s\n"

        views_updated = []
        for id, value in dict(self.state_out).items():
            if value is None:
                continue

            if state_in.get(id) != value:
                df = DesignFormat.by_id(id)
                assert df is not None
                views_updated.append(df.value.name)

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
