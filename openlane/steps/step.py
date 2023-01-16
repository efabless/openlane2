import os
import time
import subprocess
from typing import List, Callable, Optional

from .state import State, DesignFormat, Output
from ..config import Config
from ..common import mkdirp, console, error

StepConditionLambda = Callable[[Config], bool]


def get_script_dir():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scripts",
    )


class MissingInputError(ValueError):
    pass


REPORT_START_LOCUS = "%OL_CREATE_REPORT"
REPORT_END_LOCUS = "%OL_END_REPORT"


class Step(object):
    """
    Default Step Object

    Does nothing.
    """

    def __init__(self, config: Config, ordinal: Optional[int] = None):
        self.ordinal = ordinal
        self.start_time = None
        self.end_time = None
        self.config = config.copy()

    def __call__(
        self,
        state_in: State,
        run_dir: str,
        prefix: Optional[str] = None,
        **kwargs,
    ) -> State:
        step_dir = os.path.join(
            run_dir, f"{prefix or ''}{self.__class__.__name__.lower()}"
        )
        mkdirp(step_dir)
        self.start_time = time.time()
        altered_state = self.run(state_in, step_dir=step_dir, **kwargs)
        self.end_time = time.time()
        return altered_state

    def run(self, state_in: State, step_dir: str, **kwargs) -> State:
        for input in self.inputs:
            value = state_in.get(input.name)
            if value is None:
                raise MissingInputError(
                    f"{type(self).__name__}: missing required input '{input.name}'"
                )

        return state_in.copy()

    def execute(
        self,
        cmd,
        log_to: Optional[str] = None,
        step_dir: Optional[str] = None,
        **kwargs,
    ):
        if self.ordinal is not None:
            console.rule(f"{self.ordinal} - {self.__class__.__name__}")
        else:
            console.rule(f"{self.__class__.__name__}")
        log_file = open(os.devnull, "w")
        if log_to is not None:
            log_file.close()
            log_file = open(log_to, "w")

        kwargs = kwargs.copy()
        process = subprocess.Popen(
            cmd,
            encoding="utf8",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            **kwargs,
        )
        current_rpt = None
        while line := process.stdout.readline():
            if step_dir is not None and line.startswith(REPORT_START_LOCUS):
                report_name = line[len(REPORT_START_LOCUS) + 1 :].strip()
                report_path = os.path.join(step_dir, report_name)
                current_rpt = open(report_path, "w")
            elif line.startswith(REPORT_END_LOCUS):
                current_rpt.close()
                current_rpt = None
            elif current_rpt is not None:
                current_rpt.write(line)
            else:
                console.print(line.strip())
                log_file.write(line)
        returncode = process.wait()
        if returncode != 0:
            error(f"Command '{' '.join(cmd)}' failed.", _stack_offset=3)
            raise subprocess.CalledProcessError(returncode, process.args)


class TclStep(Step):
    def get_command(self, step_dir: str) -> List[str]:
        return ["tclsh"]

    @classmethod
    def get_script_path(Self) -> List[str]:
        return os.path.join(get_script_dir(), "tclsh", "hello.tcl")

    inputs: List[DesignFormat] = []
    outputs: List[Output] = []

    def run(
        self,
        state_in: State,
        step_dir: str,
        env: Optional[dict] = None,
        **kwargs,
    ) -> State:
        state = super().run(state_in, step_dir)
        command = self.get_command(step_dir)
        script = self.get_script_path()

        if env is None:
            env = os.environ.copy()

        env["SCRIPTS_DIR"] = get_script_dir()
        env["STEP_DIR"] = step_dir
        for element in self.config.keys():
            value = self.config[element]
            if value is None:
                continue
            if isinstance(value, list):
                value = " ".join(list(map(lambda x: str(x), value)))
            else:
                value = str(value)
            env[element] = value

        for input in self.inputs:
            env[f"CURRENT_{input.name}"] = state[input.name]

        for output in self.outputs:
            filename = f"{self.config['DESIGN_NAME']}.{output.format.value[0]}"
            env[f"SAVE_{output.format.name}"] = os.path.join(step_dir, filename)

        log_filename = os.path.splitext(os.path.basename(script))[0]
        log_path = os.path.join(step_dir, f"{log_filename}.log")

        self.execute(
            command + [script],
            env=env,
            log_to=log_path,
            step_dir=step_dir,
            **kwargs,
        )

        for output in self.outputs:
            if not output.update:
                continue
            state[output.format.name] = env[f"SAVE_{output.format.name}"]

        return state
