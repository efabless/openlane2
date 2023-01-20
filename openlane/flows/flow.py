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
import datetime
import subprocess
from concurrent.futures import Future, ThreadPoolExecutor
from typing import List, Tuple, Type, ClassVar, Optional, Dict, final

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
    MissingInputError,
    Step,
    State,
    TclStep,
)
from ..common import mkdirp, console, log, error, success


class Flow(object):
    name: Optional[str] = None
    Steps: ClassVar[List[Type[Step]]] = [
        TclStep,
        Step,
    ]

    def __init__(self, config_in: Config, design_dir: str):
        self.config_in: Config = config_in
        self.steps: List[Step] = []
        self.design_dir = design_dir

        self.ordinal: int = 0
        self.max_stage: int = 0
        self.task_id: Optional[TaskID] = None
        self.progress: Optional[Progress] = None
        self.run_dir: Optional[str] = None
        self.tpe: ThreadPoolExecutor = ThreadPoolExecutor()

    @classmethod
    def get_name(Self) -> str:
        return Self.name or Self.__name__

    def set_stage_count(self, count: int):
        if self.progress is None or self.task_id is None:
            return
        self.max_stage = count
        self.progress.update(self.task_id, total=count)

    def start_stage(self, name: str):
        if self.progress is None or self.task_id is None:
            return
        self.ordinal += 1
        self.progress.update(
            self.task_id,
            description=f"{self.get_name()} - Stage {self.ordinal} - {name}",
        )

    def end_stage(self):
        self.progress.update(self.task_id, completed=float(self.ordinal))

    def current_stage_prefix(self) -> str:
        max_stage_digits = len(str(self.max_stage))
        return f"%0{max_stage_digits}d-" % self.ordinal

    def dir_for_step(self, step: Step):
        if self.run_dir is None:
            raise Exception("")
        return os.path.join(
            self.run_dir,
            f"{self.current_stage_prefix()}{step.get_name_escaped()}",
        )

    @final
    def start(
        self,
        with_initial_state: Optional[State] = None,
        tag: Optional[str] = None,
    ) -> Tuple[bool, List[State]]:
        if tag is None:
            tag = datetime.datetime.now().astimezone().strftime("RUN_%Y-%m-%d_%H-%M-%S")

        self.run_dir = os.path.join(self.design_dir, "runs", tag)

        mkdirp(self.run_dir)

        config_res_path = os.path.join(self.run_dir, "resolved.json")
        with open(config_res_path, "w") as f:
            f.write(self.config_in.dumps())

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
            with_initial_state=with_initial_state,
        )
        self.progress.stop()

        # Reset stateful objects
        self.progress = None
        self.task_id = None
        self.ordinal = 0
        self.max_stage = 0

        return result

    def run(
        self,
        with_initial_state: Optional[State] = None,
    ) -> Tuple[bool, List[State]]:
        raise NotImplementedError()

    def run_step_async(self, step: Step, *args, **kwargs) -> Future[State]:
        return self.tpe.submit(step.start, *args, **kwargs)


class SequentialFlow(Flow):
    @classmethod
    def prefix(Self, ordinal: int) -> str:
        return f"%0{len(Self.Steps)}d-" % ordinal

    def run(
        self,
        with_initial_state: Optional[State] = None,
    ) -> Tuple[bool, List[State]]:
        step_count = len(self.Steps)
        self.set_stage_count(step_count)

        initial_state = with_initial_state or State()
        state_list = [initial_state]
        log("Starting…")
        for cls in self.Steps:
            step = cls()
            self.steps.append(step)
            self.start_stage(step.get_name())
            try:
                new_state = step.start()
            except MissingInputError as e:
                error(f"Misconfigured flow: {e}")
                return (False, state_list)
            except subprocess.CalledProcessError:
                error("An error has been encountered. The flow will stop.")
                return (False, state_list)
            state_list.append(new_state)
            self.end_stage()
        success("Flow complete.")
        return (True, state_list)


class FlowFactory(object):
    registry: ClassVar[Dict[str, Type[Flow]]] = {}

    @classmethod
    def register(Self, flow: Type[Flow]):
        name = flow.__name__
        Self.registry[name] = flow

    @classmethod
    def get(Self, name: str) -> Optional[Type[Flow]]:
        return Self.registry.get(name)

    @classmethod
    def list(Self) -> List[str]:
        return list(Self.registry.keys())
