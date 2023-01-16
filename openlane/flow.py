import os
import datetime
import subprocess
from typing import List, Tuple, Type, ClassVar, Optional

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
    State,
    TclStep,
    Synthesis,
    Floorplan,
    NetlistSTA,
)
from .common import mkdirp, console, error, success


class Flow(object):
    Steps: ClassVar[List[Type[Step]]] = [
        TclStep,
        Step,
    ]

    def __init__(self, config_in: Config, design_dir: str):
        self.config_in: Config = config_in
        self.steps: List[Step] = []
        self.design_dir = design_dir

    def run(
        self,
        with_initial_state: Optional[State] = None,
        tag: Optional[str] = None,
    ) -> Tuple[bool, List[State]]:
        flow_name = self.__class__.__name__
        if tag is None:
            tag = datetime.datetime.now().astimezone().strftime("RUN_%Y-%m-%d_%H-%M-%S")

        run_dir = os.path.join(self.design_dir, "runs", tag)

        mkdirp(run_dir)

        config_res_path = os.path.join(run_dir, "resolved.json")
        with open(config_res_path, "w") as f:
            f.write(self.config_in.to_json())

        step_count = len(self.Steps)
        max_digits = len(str())
        prefix = lambda ordinal: f"%0{max_digits}d-" % ordinal

        initial_state = with_initial_state or State()
        state_list = [initial_state]
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as p:
            p.log("Starting…")
            id = p.add_task(f"{flow_name}", total=step_count)
            for _i, Step in enumerate(self.Steps):
                i = _i + 1

                prev_state = state_list[-1]

                step = Step(
                    self.config_in,
                    prev_state,
                    run_dir,
                    prefix=prefix(i),
                    ordinal=i,
                )
                self.steps.append(step)

                p.update(id, description=f"{flow_name} - Step {i} - {step.get_name()}")
                try:
                    new_state = step.start()
                except MissingInputError as e:
                    error(f"Misconfigured flow: {e}")
                    return False
                except subprocess.CalledProcessError:
                    error("An error has been encountered. The flow will stop.")
                    return False
                state_list.append(new_state)
                p.update(id, completed=float(i))
        success("Flow complete.")
        return True


class Prototype(Flow):
    Steps: ClassVar[List[Type[Step]]] = [
        TclStep,
        Synthesis,
        NetlistSTA,
        Floorplan,
    ]
