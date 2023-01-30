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
import json
from typing import List
from abc import abstractmethod

from .tclstep import TclStep
from .state import State
from .design_format import DesignFormat
from ..common import get_script_dir


class YosysStep(TclStep):
    def get_command(self) -> List[str]:
        return ["yosys", "-c", self.get_script_path()]

    @abstractmethod
    def get_script_path(self):
        pass


class Synthesis(YosysStep):
    inputs = []  # The input RTL is part of the configuration
    outputs = [DesignFormat.NETLIST]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "yosys", "synthesize.tcl")

    def run(
        self,
        **kwargs,
    ) -> State:
        assert isinstance(self.config["LIB"], list)

        kwargs, env = self.extract_env(kwargs)

        lib_synth = self.toolbox.remove_cells_from_lib(
            frozenset(self.config["LIB"]),
            excluded_cells=frozenset(
                [
                    self.config["BAD_CELL_LIST"],
                    self.config["NO_SYNTH_CELL_LIST"],
                ]
            ),
            as_cell_lists=True,
        )

        env["LIB_SYNTH"] = lib_synth
        state_out = super().run(env=env, **kwargs)

        stats_file = os.path.join(self.step_dir, "reports", "stat.json")
        stats_str = open(stats_file).read()
        stats = json.loads(stats_str)

        state_out.metrics["design__instance__count"] = stats["design"]["num_cells"]
        if chip_area := stats["design"].get("area"):  # needs nonzero area
            state_out.metrics["design__instance__area"] = chip_area

        return state_out
