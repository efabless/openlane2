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
from typing import List, Tuple, Type, ClassVar, Optional, Dict, final, Callable

from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    MofNCompleteColumn,
    TimeElapsedColumn,
    TaskID,
)

from ..config import Config
from ..steps import (
    Step,
    TclStep,
    State,
)
from ..utils import Toolbox
from ..common import mkdirp, console, log


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

    Properties:

        :param name: An optional string name for the flow
        :param Steps: A list of Step **types** used by the Flow (not Step objects.)
    """

    name: Optional[str] = None
    Steps: List[Type[Step]] = [
        TclStep,
    ]

    def __init__(self, config: Config, design_dir: str):
        """
        :param config: The configuration object used for this flow.
        :param design_dir: The design directory of the flow, i.e., the `dirname`
            of the `config.json` file from which it was generated.
        """
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

    def get_name(self) -> str:
        """
        :returns: The name of the Flow. If `self.name` is None, the class's name
            is returned.
        """
        return self.name or self.__class__.__name__

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

    def start_stage(self, name: str):
        """
        Starts a new stage, updating the progress bar appropriately.

        :param name: The name of the stage.
        """
        if self.progress is None or self.task_id is None:
            return
        self.progress.update(
            self.task_id,
            description=f"{self.get_name()} - Stage {self.ordinal} - {name}",
        )

    def end_stage(self, no_increment_ordinal: bool = False):
        """
        Ends the current stage, updating the progress bar appropriately.
        """
        self.completed += 1
        if not no_increment_ordinal:
            self.ordinal += 1
        assert self.progress is not None and self.task_id is not None
        self.progress.update(self.task_id, completed=float(self.completed))

    def current_stage_prefix(self) -> str:
        """
        Returns a prefix for a step ID with its stage number so it can be used
        to create a step directory.
        """
        max_stage_digits = len(str(self.max_stage))
        return f"%0{max_stage_digits}d-" % self.ordinal

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
            f"{self.current_stage_prefix()}{step.id}",
        )

    @final
    def start(
        self,
        with_initial_state: Optional[State] = None,
        tag: Optional[str] = None,
        **kwargs,
    ) -> Tuple[List[State], List[Step]]:
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

        initial_state = State()

        try:
            entries = os.listdir(self.run_dir)
            if len(entries) == 0:
                raise FileNotFoundError(self.run_dir)  # Treat as non-existent directory
            log(f"Using existing run at '{tag}' with the '{self.get_name()}' flow.")

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
            log(
                f"Starting a new run of the '{self.get_name()}' flow with the tag '{tag}'."
            )
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
            f"{self.get_name()}",
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

    @abstractmethod
    def run(
        self,
        initial_state: State,
        **kwargs,
    ) -> Tuple[List[State], List[Step]]:
        """
        The core of the Flow. Subclasses of flow are expected to override this
        method.

        This method is considered private and should only be called by Flow or
        its subclasses.

        :param initial_state: An initial state object to use.
        :returns: `(success, state_list)`
        """
        pass

    def run_step_async(self, step: Step, *args, **kwargs) -> Future[State]:
        """
        A helper function that may run a step asynchronously.

        It returns a `Future` encapsulating a State object, which can then be
        used as an input to the next step or inspected to await it.

        See the Step initializer for more info.

        :param step: The step object to run
        :param args: Arguments to `step.start`
        :param kwargs: Keyword arguments to `step.start`
        """
        return self.tpe.submit(step.start, *args, **kwargs)

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
            Adds a flow type to the registry.

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
            :returns: A list of strings representing all registered
            flows.
            """
            return list(Self._registry.keys())

    factory = FlowFactory
