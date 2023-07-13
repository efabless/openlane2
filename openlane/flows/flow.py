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
import glob
import datetime
import textwrap
from abc import abstractmethod, ABC
from concurrent.futures import Future
from functools import wraps
from typing import (
    List,
    Sequence,
    Tuple,
    Type,
    ClassVar,
    Optional,
    Dict,
    Callable,
    TypeVar,
    Union,
)

from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    MofNCompleteColumn,
    TimeElapsedColumn,
    TaskID,
)
from deprecated.sphinx import deprecated

from ..config import (
    Config,
    Variable,
    universal_flow_config_variables,
)
from ..state import State
from ..steps import Step
from ..utils import Toolbox
from ..logging import console, info, verbose
from ..common import get_tpe, mkdirp, protected, final, slugify


class FlowError(RuntimeError):
    """
    A ``RuntimeError`` that occurs when a Flow, or one of its underlying Steps,
    fails to finish execution properly.
    """

    pass


class FlowException(FlowError):
    """
    A variant of :class:`FlowError` for unexpected failures or failures due
    to misconfiguration, such as:

    * A :class:`StepException` raised by an underlying Step
    * Invalid inputs
    * Mis-use of class interfaces of the :class:`Flow`
    * Other unexpected failures
    """

    pass


T = TypeVar("T", bound=Callable)


def ensure_progress_started(method: T) -> Callable:
    """
    If a method of :class:`FlowProgressBar`decorated with `ensure_started`
    and :meth:`start` had not been called yet, a :class:`FlowException` will be
    thrown.

    The docstring will also be amended to reflect that fact.

    :param method: The method of :class:`FlowProgressBar` in question.
    """

    @wraps(method)
    def _impl(obj: FlowProgressBar, *method_args, **method_kwargs):
        if not obj.started:
            raise FlowException(
                f"Attempted to call method '{method}' before initializing progress bar"
            )
        return method(obj, *method_args, **method_kwargs)

    if method.__doc__ is None:
        method.__doc__ = ""

    method.__doc__ = (
        "This method may not be called before the progress bar is started.\n"
        + method.__doc__
    )

    return _impl


class FlowProgressBar(object):
    """
    A wrapper for a flow's progress bar, rendered using Rich at the bottom of
    interactive terminals.
    """

    def __init__(self, flow_name: str, starting_ordinal: int = 1) -> None:
        self.__flow_name: str = flow_name
        self.__stages_completed: int = 0
        self.__max_stage: int = 0
        self.__task_id: TaskID = TaskID(-1)
        self.__ordinal: int = starting_ordinal
        self.__progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        )

    def start(self):
        """
        Starts rendering the progress bar.
        """
        self.__progress.start()
        self.__task_id = self.__progress.add_task(
            f"{self.__flow_name}",
        )

    def end(self):
        """
        Stops rendering the progress bar.
        """
        self.__progress.stop()
        self.__task_id = TaskID(-1)

    @property
    def started(self) -> bool:
        """
        :returns: If the progress bar has started or not
        """
        return self.__task_id != TaskID(-1)

    @ensure_progress_started
    def set_max_stage_count(self, count: int):
        """
        A helper function, used to set the total number of stages the progress
        bar is expected to keep tally of.

        :param count: The total number of stages.
        """
        self.__max_stage = count
        self.__progress.update(self.__task_id, total=count)

    @ensure_progress_started
    def start_stage(self, name: str):
        """
        Starts a new stage, updating the progress bar appropriately.

        :param name: The name of the stage.
        """
        self.__progress.update(
            self.__task_id,
            description=f"{self.__flow_name} - Stage {self.__stages_completed + 1} - {name}",
        )

    @ensure_progress_started
    def end_stage(self, *, increment_ordinal: bool = True):
        """
        Ends the current stage, updating the progress bar appropriately.

        :param increment_ordinal: Increment the step ordinal, which is used in the creation of step directories.

            You may want to set this to ``False`` if the stage is being skipped.

            Please note that step ordinal is not equal to stages- a skipped step
            increments the stage but not the step ordinal.
        """
        self.__stages_completed += 1
        if increment_ordinal:
            self.__ordinal += 1
        self.__progress.update(self.__task_id, completed=float(self.__stages_completed))

    @ensure_progress_started
    def get_ordinal_prefix(self) -> str:
        """
        Returns a string with the current step ordinal, which can be used to
        create a step directory.
        """
        max_stage_digits = len(str(self.__max_stage))
        return f"%0{max_stage_digits}d-" % self.__ordinal


class Flow(ABC):
    """
    An abstract base class for a flow.

    Flows encapsulates a subroutine that runs multiple steps: either synchronously,
    asynchronously, serially or in any manner.

    The Flow ABC offers a number of convenience functions, including handling the
    progress bar at the bottom of the terminal, which shows what stage the flow
    is currently in and the remaining stages.

    :param config: Either a resolved :class:`Config` object, or an input to
        :meth:`Config.load`.

    :param name: An optional string name for the Flow itself, and not a run of it.

        If not set, the Python class name will be used instead.

    :param config_override_strings: See :meth:`Config.load`
    :param pdk: See :meth:`Config.load`
    :param pdk_root: See :meth:`Config.load`
    :param scl: See :meth:`Config.load`
    :param design_dir: See :meth:`Config.load`

    :ivar Steps:
        A list of :class:`Step` **types** used by the Flow (not Step objects.)

        Subclasses of :class:`Step` are expected to override the default value
        as a class member- but subclasses may allow this value to be further
        overridden during construction (and only then.)

    :ivar step_objects:
        A list of :class:`Step` **objects** from the last run of the flow,
        if it exists.

        If :meth:`start` is called again, the reference is destroyed.

    :ivar run_dir:
        The directory of the last run of the flow, if it exists.

        If :meth:`start` is called again, the reference is destroyed.

    :ivar toolbox:
        The :class:`Toolbox` of the last run of the flow, if it exists.

        If :meth:`start` is called again, the reference is destroyed.
    """

    name: str
    Steps: List[Type[Step]] = []  # Override
    step_objects: Optional[List[Step]] = None
    run_dir: Optional[str] = None
    toolbox: Optional[Toolbox] = None

    def __init__(
        self,
        config: Union[Config, str, os.PathLike, Dict],
        *,
        name: Optional[str] = None,
        pdk: Optional[str] = None,
        pdk_root: Optional[str] = None,
        scl: Optional[str] = None,
        design_dir: Optional[str] = None,
        config_override_strings: Optional[Sequence[str]] = None,
    ):
        self.name = name or self.__class__.__name__

        self.Steps = self.Steps.copy()  # Break global reference

        if not isinstance(config, Config):
            config, design_dir = Config.load(
                config_in=config,
                flow_config_vars=self.get_config_variables(),
                config_override_strings=config_override_strings,
                pdk=pdk,
                pdk_root=pdk_root,
                scl=scl,
                design_dir=design_dir,
            )

        self.config: Config = config
        self.design_dir: str = str(self.config["DESIGN_DIR"])
        self.progress_bar = FlowProgressBar(self.name)

    @classmethod
    def get_help_md(Self):
        """
        Renders Markdown help for this flow to a string.
        """
        doc_string = ""
        if Self.__doc__:
            doc_string = textwrap.dedent(Self.__doc__)

        result = (
            textwrap.dedent(
                f"""\
                ### {Self.__name__}

                ```{{eval-rst}}
                %s
                ```

                #### Using from the CLI

                ```sh
                openlane --flow {Self.__name__} [...]
                ```

                #### Importing

                ```python
                from openlane.flows import Flow

                {Self.__name__} = Flow.factory.get("{Self.__name__}")
                ```
                """
            )
            % doc_string
        )
        if len(Self.Steps):
            result += "#### Included Steps\n"
            for step in Self.Steps:
                result += f"* [`{step.id}`](./step_config_vars.md#{step.id})\n"

        return result

    def get_config_variables(self) -> List[Variable]:
        flow_variables_by_name: Dict[str, Tuple[Variable, str]] = {
            variable.name: (variable, "Universal")
            for variable in universal_flow_config_variables
        }
        for step_cls in self.Steps:
            for variable in step_cls.config_vars:
                if flow_variables_by_name.get(variable.name) is not None:
                    existing_variable, existing_step = flow_variables_by_name[
                        variable.name
                    ]
                    if variable != existing_variable:
                        raise FlowException(
                            f"Misconfigured flow: Unrelated variables in {existing_step} and {step_cls.__name__} share a name: {variable.name}"
                        )
                flow_variables_by_name[variable.name] = (variable, step_cls.__name__)

        return [variable for variable, _ in flow_variables_by_name.values()]

    @classmethod
    @deprecated(
        version="2.0.0-a29",
        reason="Use the constructor for the class instead",
        action="once",
    )
    def init_with_config(
        Self,
        config_in: Union[Config, str, os.PathLike, Dict],
        **kwargs,
    ):
        kwargs["config"] = config_in
        return Self(**kwargs)

    @final
    def start(
        self,
        with_initial_state: Optional[State] = None,
        tag: Optional[str] = None,
        last_run: bool = False,
        **kwargs,
    ) -> State:
        """
        The entry point for a flow.

        :param with_initial_state: An optional initial state object to use.
            If not provided:
            * If resuming a previous run, the latest ``state_out.json`` (by filesystem modification date)
            * If not, an empty state object is created.
        :param tag: A name for this invocation of the flow. If not provided,
            one based on a date string will be created.

            This tag is used to create the "run directory", which will be placed
            under the directory ``runs/`` in the design directory.

        :returns: ``(success, state_list)``
        """
        if last_run:
            if tag is not None:
                raise FlowException(
                    "tag and last_run cannot be defined simultaneously."
                )

            runs = glob.glob(os.path.join(self.design_dir, "runs", "*"))

            latest_time: float = 0
            latest_run: Optional[str] = None
            for run in runs:
                time = os.path.getmtime(run)
                if time > latest_time:
                    latest_time = time
                    latest_run = run

            if latest_run is not None:
                tag = os.path.basename(latest_run)

        if tag is None:
            tag = datetime.datetime.now().astimezone().strftime("RUN_%Y-%m-%d_%H-%M-%S")

        # Stored until next start()
        self.run_dir = os.path.join(self.design_dir, "runs", tag)
        # Stored until next start()
        self.toolbox = Toolbox(os.path.join(self.run_dir, "tmp"))

        initial_state = with_initial_state or State()

        starting_ordinal = 1
        try:
            entries = os.listdir(self.run_dir)
            if len(entries) == 0:
                raise FileNotFoundError(self.run_dir)  # Treat as non-existent directory
            info(f"Using existing run at '{tag}' with the '{self.name}' flow.")

            # Extract maximum step ordinal
            for entry in entries:
                components = entry.split("-")
                if len(components) < 2:
                    continue
                try:
                    extracted_ordinal = int(components[0])
                except ValueError:
                    continue
                starting_ordinal = max(starting_ordinal, extracted_ordinal + 1)

            # Extract Maximum State
            if with_initial_state is None:
                latest_time = 0
                latest_json: Optional[str] = None
                state_out_jsons = glob.glob(
                    os.path.join(self.run_dir, "**", "state_out.json"), recursive=True
                )
                for state_out_json in state_out_jsons:
                    time = os.path.getmtime(state_out_json)
                    if time > latest_time:
                        latest_time = time
                        latest_json = state_out_json

                verbose(f"Using state at '{latest_json}'.")

                if latest_json is not None:
                    initial_state = State.loads(
                        open(latest_json, encoding="utf8").read()
                    )

        except NotADirectoryError:
            raise FlowException(
                f"Run directory for '{tag}' already exists as a file and not a directory."
            )
        except FileNotFoundError:
            info(f"Starting a new run of the '{self.name}' flow with the tag '{tag}'.")
            mkdirp(self.run_dir)

        config_res_path = os.path.join(self.run_dir, "resolved.json")
        with open(config_res_path, "w") as f:
            f.write(self.config.dumps())

        self.progress_bar = FlowProgressBar(self.name)
        self.progress_bar.start()
        final_state, step_objects = self.run(
            initial_state=initial_state,
            starting_ordinal=starting_ordinal,
            **kwargs,
        )
        self.progress_bar.end()

        # Stored until next start()
        self.step_objects = step_objects

        return final_state

    @protected
    @abstractmethod
    def run(
        self,
        initial_state: State,
        **kwargs,
    ) -> Tuple[State, List[Step]]:
        """
        The core of the Flow. Subclasses of flow are expected to override this
        method.

        :param initial_state: An initial state object to use.
        :returns: A tuple of states and instantiated step objects for inspection.
        """
        pass

    @protected
    def dir_for_step(self, step: Step) -> str:
        """
        Returns a directory within the run directory for a specific step,
        prefixed with the current progress bar stage number.

        May only be called while :attr:`run_dir` is not None, i.e., the flow
        has started.
        """
        if self.run_dir is None:
            raise FlowException(
                "Attempted to call dir_for_step on a flow that has not been started."
            )
        return os.path.join(
            self.run_dir,
            f"{self.progress_bar.get_ordinal_prefix()}{slugify(step.id)}",
        )

    @protected
    def start_step(
        self,
        step: Step,
        *args,
        **kwargs,
    ) -> State:
        """
        A helper function that handles passing parameters to :mod:`Step.start`.'

        It is essentially equivalent to:

        .. code-block:: python

            step.start(
                toolbox=self.toolbox,
                step_dir=self.dir_for_step(step),
            )


        See :meth:`Step.start` for more info.

        :param step: The step object to run
        :param args: Arguments to `step.start`
        :param kwargs: Keyword arguments to `step.start`
        """

        kwargs["toolbox"] = self.toolbox
        kwargs["step_dir"] = self.dir_for_step(step)

        return step.start(*args, **kwargs)

    @protected
    def start_step_async(
        self,
        step: Step,
        *args,
        **kwargs,
    ) -> Future[State]:
        """
        An asynchronous equivalent to :meth:`start_step`.

        It returns a ``Future`` encapsulating a State object, which can then be
        used as an input to the next step or inspected to await it.

        :param step: The step object to run
        :param args: Arguments to `step.start`
        :param kwargs: Keyword arguments to `step.start`
        """

        kwargs["toolbox"] = self.toolbox
        kwargs["step_dir"] = self.dir_for_step(step)

        return get_tpe().submit(step.start, *args, **kwargs)

    @deprecated(
        version="2.0.0a46",
        reason="Use .progress_bar.set_max_stage_count",
        action="once",
    )
    @protected
    def set_max_stage_count(self, count: int):
        """
        Alias for ``self.progress_bar``'s :py:meth:`FlowProgressBar.set_max_stage_count`.
        """
        self.progress_bar.set_max_stage_count(count)

    @deprecated(
        version="2.0.0a46", reason="Use .progress_bar.start_stage", action="once"
    )
    @protected
    def start_stage(self, name: str):
        """
        Alias for ``self.progress_bar``'s :py:meth:`FlowProgressBar.start_stage`.
        """
        self.progress_bar.start_stage(name)

    @deprecated(version="2.0.0a46", reason="Use .progress_bar.end_stage", action="once")
    @protected
    def end_stage(self, increment_ordinal: bool = True):
        """
        Alias for ``self.progress_bar``'s :py:meth:`FlowProgressBar.end_stage`.
        """
        self.progress_bar.end_stage(increment_ordinal=increment_ordinal)

    class FlowFactory(object):
        """
        A factory singleton for Flows, allowing Flow types to be registered and then
        retrieved by name.

        See https://en.wikipedia.org/wiki/Factory_(object-oriented_programming) for
        a primer.
        """

        __registry: ClassVar[Dict[str, Type[Flow]]] = {}

        @classmethod
        def register(
            Self, registered_name: Optional[str] = None
        ) -> Callable[[Type[Flow]], Type[Flow]]:
            """
            A decorator that adds a flow type to the registry.

            :param registered_name: An optional registered name for the flow.

                If not specified, the flow will be referred to by its Python
                class name.
            """

            def decorator(cls: Type[Flow]) -> Type[Flow]:
                name = cls.__name__
                if registered_name is not None:
                    name = registered_name
                Self.__registry[name] = cls
                return cls

            return decorator

        @classmethod
        def get(Self, name: str) -> Optional[Type[Flow]]:
            """
            Retrieves a Flow type from the registry using a lookup string.

            :param name: The registered name of the Flow. Case-sensitive.
            """
            return Self.__registry.get(name)

        @classmethod
        def list(Self) -> List[str]:
            """
            :returns: A list of strings representing all registered flows.
            """
            return list(Self.__registry.keys())

    factory = FlowFactory
