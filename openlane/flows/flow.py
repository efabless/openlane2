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
from abc import abstractmethod, ABC
from concurrent.futures import Future, ThreadPoolExecutor
from typing import (
    List,
    Sequence,
    Tuple,
    Type,
    ClassVar,
    Optional,
    Dict,
    Callable,
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

from ..config import (
    Config,
    ConfigBuilder,
    Variable,
    universal_flow_config_variables,
)
from ..state import State
from ..steps import Step
from ..utils import Toolbox
from ..logging import console, info
from ..common import mkdirp, internal, final, slugify


class FlowException(RuntimeError):
    pass


class FlowError(RuntimeError):
    pass


class FlowImplementationError(RuntimeError):
    pass


class Flow(ABC):
    """
    An abstract base class for a flow.

    Flows encapsulates a subroutine that runs multiple steps: either synchronously,
    asynchronously, serially or in any manner.

    The Flow ABC offers a number of convenience functions, including handling the
    progress bar at the bottom of the terminal, which shows what stage the flow
    is currently in and the remaining stages.

    :param config: A resolved OpenLane configuration object to be used as input
        for this instance of a flow.
    :param design_dir: A design directory
    :param name: An optional string name for the Flow itself, and not a run of it.

        If not set, the Python class name will be used instead.
    :param Steps:
        A list of :class:`Step` **types** used by the Flow (not Step objects.)

        Subclasses of :class:`Step` are expected to override the default value
        as a class member.
    """

    name: str
    Steps: List[Type[Step]] = []  # Override

    def __init__(
        self,
        config: Config,
        design_dir: str,
        name: Optional[str] = None,
        Steps: Optional[List[Type[Step]]] = None,
    ):
        if Steps is not None:
            self.Steps = Steps

        self.name = name or self.__class__.__name__
        self.config: Config = config
        self.design_dir = design_dir

        self.tpe: ThreadPoolExecutor = ThreadPoolExecutor()

        self.ordinal: int = 1
        self.completed: int = 0
        self.max_stage: int = 0
        self.task_id: Optional[TaskID] = None
        self.progress: Optional[Progress] = None
        self.run_dir: Optional[str] = None
        self.tmp_dir: Optional[str] = None
        self.toolbox: Optional[Toolbox] = None

    @classmethod
    def get_config_variables(Self) -> List[Variable]:
        flow_variables_by_name: Dict[str, Tuple[Variable, str]] = {
            variable.name: (variable, "Universal")
            for variable in universal_flow_config_variables
        }
        for step_cls in Self.Steps:
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
    def init_with_config(
        Self,
        config_in: Union[str, os.PathLike, Dict],
        pdk: Optional[str] = None,
        pdk_root: Optional[str] = None,
        scl: Optional[str] = None,
        design_dir: Optional[str] = None,
        config_override_strings: Optional[Sequence[str]] = None,
        **kwargs,
    ):
        """
        Create a new instance of the :class:`Flow` object with a given
        configuration file or object.

        :param config_in: See :meth:`ConfigBuilder.load`
        :param config_override_strings: See :meth:`ConfigBuilder.load`
        :param pdk: See :meth:`ConfigBuilder.load`
        :param pdk_root: See :meth:`ConfigBuilder.load`
        :param scl: See :meth:`ConfigBuilder.load`
        :param design_dir: See :meth:`ConfigBuilder.load`
        """

        flow_config_vars = Self.get_config_variables()

        config_resolved, design_dir_resolved = ConfigBuilder.load(
            config_in=config_in,
            flow_config_vars=flow_config_vars,
            config_override_strings=config_override_strings,
            pdk=pdk,
            pdk_root=pdk_root,
            scl=scl,
            design_dir=design_dir,
        )

        return Self(
            config=config_resolved,
            design_dir=design_dir_resolved,
            **kwargs,
        )

    @final
    def start(
        self,
        with_initial_state: Optional[State] = None,
        tag: Optional[str] = None,
        **kwargs,
    ) -> Tuple[State, List[Step]]:
        """
        The entry point for a flow.

        :param with_initial_state: An optional initial state object to use.
            If not provided:
            * If resuming a previous run, the latest `state_out.json` (by filesystem modification date)
            * If not, an empty state object is created.
        :param tag: A name for this invocation of the flow. If not provided,
            one based on a date string will be created.

        :returns: `(success, state_list)`
        """
        if tag is None:
            tag = datetime.datetime.now().astimezone().strftime("RUN_%Y-%m-%d_%H-%M-%S")

        self.run_dir = os.path.join(self.design_dir, "runs", tag)
        self.tmp_dir = os.path.join(self.run_dir, "tmp")
        self.toolbox = Toolbox(self.tmp_dir)

        initial_state = with_initial_state or State()

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
                    current_ordinal = int(components[0])
                except ValueError:
                    continue
                self.ordinal = max(self.ordinal, current_ordinal + 1)

            # Extract Maximum State
            if with_initial_state is None:
                latest_time: float = 0
                latest_json: Optional[str] = None
                state_out_jsons = glob.glob(
                    os.path.join(self.run_dir, "**", "state_out.json"), recursive=True
                )
                for state_out_json in state_out_jsons:
                    time = os.path.getmtime(state_out_json)
                    if time > latest_time:
                        latest_time = time
                        latest_json = state_out_json

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

        self.progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        )
        self.progress.start()
        self.task_id = self.progress.add_task(
            f"{self.name}",
        )
        result = self.run(
            initial_state=initial_state,
            **kwargs,
        )
        self.progress.stop()

        # Reset stateful objects
        self.progress = None
        self.task_id = None
        self.tmp_dir = None
        self.toolbox = None
        self.ordinal = 1
        self.completed = 0
        self.max_stage = 0

        return result

    @internal
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

    @internal
    def start_step_async(
        self,
        step: Step,
        toolbox: Optional[Toolbox] = None,
        *args,
        **kwargs,
    ) -> Future[State]:
        """
        A helper function that may run a step asynchronously.

        It returns a `Future` encapsulating a State object, which can then be
        used as an input to the next step or inspected to await it.

        See the Step initializer for more info.

        :param step: The step object to run
        :param toolbox: An optional override for the flow's :class:`Toolbox`.
            If you don't know what this means, just leave this as ``None``.
        :param args: Arguments to `step.start`
        :param kwargs: Keyword arguments to `step.start`
        """

        kwargs["toolbox"] = toolbox or self.toolbox

        return self.tpe.submit(step.start, *args, **kwargs)

    @internal
    def set_max_stage_count(self, count: int):
        """
        A helper function, used to set the total number of stages a flow is
        expected to go through. Used to set the progress bar.

        :param count: The total number of stages.
        """
        if self.progress is None or self.task_id is None:
            return
        self.max_stage = count
        self.progress.update(self.task_id, total=count)

    @internal
    def start_stage(self, name: str):
        """
        Starts a new stage, updating the progress bar appropriately.

        :param name: The name of the stage.
        """
        if self.progress is None or self.task_id is None:
            return
        self.progress.update(
            self.task_id,
            description=f"{self.name} - Stage {self.ordinal} - {name}",
        )

    @internal
    def end_stage(self, no_increment_ordinal: bool = False):
        """
        Ends the current stage, updating the progress bar appropriately.
        """
        self.completed += 1
        if not no_increment_ordinal:
            self.ordinal += 1
        assert self.progress is not None and self.task_id is not None
        self.progress.update(self.task_id, completed=float(self.completed))

    @internal
    def current_stage_prefix(self) -> str:
        """
        Returns a prefix for a step ID with its stage number so it can be used
        to create a step directory.
        """
        max_stage_digits = len(str(self.max_stage))
        return f"%0{max_stage_digits}d-" % self.ordinal

    @internal
    def dir_for_step(self, step: Step):
        """
        Returns a directory within the run directory for a specific step,
        prefixed with the current progress bar stage number.
        """
        if self.run_dir is None:
            raise FlowImplementationError(
                "Attempted to call dir_for_step before starting flow."
            )
        return os.path.join(
            self.run_dir,
            f"{self.current_stage_prefix()}{slugify(step.id)}",
        )

    class FlowFactory(object):
        """
        A factory singleton for Flows, allowing Flow types to be registered and then
        retrieved by name.

        See https://en.wikipedia.org/wiki/Factory_(object-oriented_programming) for
        a primer.
        """

        _registry: ClassVar[Dict[str, Type[Flow]]] = {}

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
                Self._registry[name] = cls
                return cls

            return decorator

        @classmethod
        def get(Self, name: str) -> Optional[Type[Flow]]:
            """
            Retrieves a Flow type from the registry using a lookup string.

            :param name: The registered name of the Flow. Case-sensitive.
            """
            return Self._registry.get(name)

        @classmethod
        def list(Self) -> List[str]:
            """
            :returns: A list of strings representing all registered flows.
            """
            return list(Self._registry.keys())

    factory = FlowFactory
    get = FlowFactory.get
