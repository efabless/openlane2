import os
from typing import List

from .step import TclStep, get_script_dir
from .state import DesignFormat, Output


class Synthesis(TclStep):
    outputs = [Output(DesignFormat.NETLIST)]

    def get_command(self, step_dir: str) -> List[str]:
        return ["yosys", "-c"]

    @classmethod
    def get_script_path(Self) -> List[str]:
        return os.path.join(get_script_dir(), "yosys", "synthesize.tcl")
