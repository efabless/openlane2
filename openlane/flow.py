import os
import datetime
import subprocess
from typing import List, Tuple, Union, Type, ClassVar, Optional

from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    MofNCompleteColumn,
    TimeElapsedColumn,
)

from .config import Config
from .steps import (
    MissingInputError,
    Step,
    StepConditionLambda,
    State,
    TclStep,
    Synthesis,
    Floorplan,
    NetlistSTA,
)
from .common import mkdirp, console, error, success


class Flow(object):
    Steps: ClassVar[List[Union[Type, Tuple[Type, StepConditionLambda]]]] = [
        TclStep,
        Step,
    ]

    def __init__(self, config_in: Config):
        self.config_in: Config = config_in
        self.steps: List[Step] = []
        self.state_list: Optional[List[State]] = None
        for _i, step in enumerate(self.Steps):
            i = _i + 1
            self.steps.append(step(config_in, i))

    def run(
        self,
        design_dir: str,
        with_initial_state: Optional[State] = None,
        tag: Optional[str] = None,
    ) -> bool:
        flow_name = self.__class__.__name__
        if tag is None:
            tag = datetime.datetime.now().astimezone().strftime("RUN_%Y-%m-%d_%H-%M-%S")

        run_dir = os.path.join(design_dir, "runs", tag)

        mkdirp(run_dir)

        config_res_path = os.path.join(run_dir, "resolved.json")
        with open(config_res_path, "w") as f:
            f.write(self.config_in.to_json())

        step_count = len(self.steps)
        max_digits = len(str())
        prefix = lambda ordinal: f"%0{max_digits}d-" % ordinal

        initial_state = with_initial_state or State()
        self.state_list = [initial_state]
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as p:
            p.log("Starting…")
            id = p.add_task(f"{flow_name}", total=step_count)
            for _i, step in enumerate(self.steps):
                i = _i + 1

                step_name = step.__class__.__name__
                p.update(id, description=f"{flow_name} - Step {i} - {step_name}")
                prev_state = self.state_list[-1]
                try:
                    new_state = step(prev_state, run_dir=run_dir, prefix=prefix(i))
                except MissingInputError as e:
                    error(f"Misconfigured flow: {e}")
                except subprocess.CalledProcessError:
                    error("An error has been encountered. The flow will stop.")
                    return False
                self.state_list.append(new_state)
                p.update(id, completed=float(i))
        success("Flow complete.")
        return True


class Prototype(Flow):
    Steps: ClassVar[List[Union[Type, Tuple[Type, StepConditionLambda]]]] = [
        TclStep,
        Synthesis,
        NetlistSTA,
        Floorplan,
    ]
