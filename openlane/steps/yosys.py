import os
from typing import List

from .step import TclStep, get_script_dir
from .state import DesignFormat, Output


class Synthesis(TclStep):
    outputs = [Output(DesignFormat.NETLIST)]

    def get_command(self) -> List[str]:
        return ["yosys", "-c", self.get_script_path()]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "yosys", "synthesize.tcl")
