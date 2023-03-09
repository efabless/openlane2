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
from typing import List, Optional
from abc import abstractmethod

from .step import Step
from .tclstep import TclStep
from ..state import State
from ..state import DesignFormat
from .common_variables import constraint_variables

from ..common import get_script_dir
from ..config import Path, Variable, StringEnum


class YosysStep(TclStep):
    def get_command(self) -> List[str]:
        script_path = self.get_script_path()
        assert isinstance(script_path, str)
        return ["yosys", "-c", script_path]

    @abstractmethod
    def get_script_path(self):
        pass


@Step.factory.register()
class JsonHeader(YosysStep):
    id = "Yosys.JsonHeader"
    inputs = []
    outputs = [DesignFormat.JSON_HEADER]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "yosys", "json_header.tcl")

    config_vars = [
        Variable(
            "SYNTH_POWER_DEFINE",
            Optional[str],
            "Specifies the name of the define used to guard power and ground connections",
            deprecated_names=["SYNTH_USE_PG_PINS_DEFINES"],
        )
    ]


@Step.factory.register()
class Synthesis(YosysStep):
    id = "Yosys.Synthesis"
    inputs = []  # The input RTL is part of the configuration
    outputs = [DesignFormat.NETLIST]

    config_vars = constraint_variables + [
        Variable(
            "VERILOG_FILES",
            List[Path],
            "The paths of the design's Verilog files.",
        ),
        Variable(
            "SYNTH_AUTONAME",
            bool,
            "Generates names for  netlistinstances. This results in instance names that can be very long, but are more human-readable.",
            default=False,
        ),
        Variable(
            "SYNTH_STRATEGY",
            StringEnum(
                "SYNTH_STRATEGY",
                [
                    "AREA 0",
                    "AREA 1",
                    "AREA 2",
                    "AREA 3",
                    "AREA 4",
                    "DELAY 0",
                    "DELAY 1",
                    "DELAY 2",
                    "DELAY 3",
                    "DELAY 4",
                ],
            ),
            "Strategies for abc logic synthesis and technology mapping. AREA strategies usually result in a more compact design, while DELAY strategies usually result in a design that runs at a higher frequency. Please note that there is no way to know which strategy is the best before trying them.",
            default="AREA 0",
        ),
        Variable(
            "SYNTH_DEFINES",
            Optional[List[str]],
            "Synthesis defines",
        ),
        Variable(
            "SYNTH_BUFFERING",
            bool,
            "Enables `abc` cell buffering.",
            default=True,
        ),
        Variable(
            "SYNTH_SIZING",
            bool,
            "Enables `abc` cell sizing (instead of buffering).",
            default=False,
        ),
        Variable(
            "SYNTH_READ_BLACKBOX_LIB",
            bool,
            "A flag that enable reading the full (untrimmed) liberty file as a blackbox for synthesis. Please note that this is not used in technology mapping. This should only be used when trying to preserve gate instances in the rtl of the design.",
            default=False,
        ),
        Variable(
            "SYNTH_NO_FLAT",
            bool,
            "A flag that disables flattening the hierarchy during synthesis, only flattening it after synthesis, mapping and optimizations.",
            default=False,
        ),
        Variable(
            "SYNTH_SHARE_RESOURCES",
            bool,
            "A flag that enables yosys to reduce the number of cells by determining shareable resources and merging them.",
            default=True,
        ),
        Variable(
            "SYNTH_ADDER_TYPE",
            StringEnum("SYNTH_ADDER_TYPE", ["YOSYS", "FA", "RCA", "CSA"]),
            "Adder type to which the $add and $sub operators are mapped to.  Possible values are `YOSYS/FA/RCA/CSA`; where `YOSYS` refers to using Yosys internal adder definition, `FA` refers to full-adder structure, `RCA` refers to ripple carry adder structure, and `CSA` refers to carry select adder.",
            default="YOSYS",
        ),
        Variable(
            "SYNTH_EXTRA_MAPPING_FILE",
            Optional[Path],
            "Points to an extra techmap file for yosys that runs right after yosys `synth` before generic techmap.",
        ),
        Variable(
            "SYNTH_PARAMETERS",
            Optional[List[str]],
            "Key-value pairs to be `chparam`ed in Yosys, in the format `key1=value1`.",
        ),
        Variable(
            "SYNTH_ELABORATE_ONLY",
            bool,
            '"Elaborate" the design only without attempting any logic mapping. Useful when dealing with structural Verilog netlists.',
            default=False,
        ),
        Variable(
            "SYNTH_FLAT_TOP",
            bool,
            "Specifies whether or not the top level should be flattened during elaboration.",
            default=False,
        ),
        Variable(
            "VERILOG_INCLUDE_DIRS",
            Optional[List[str]],
            "Specifies the Verilog `include` directories.",
        ),
    ]

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

        cells = stats["design"]["num_cells_by_type"]
        unmapped_keyword = "$"
        unmapped_cells = [
            cells[y] for y in cells.keys() if y.startswith(unmapped_keyword)
        ]
        state_out.metrics["design__instance_unmapped__count"] = sum(unmapped_cells)

        return state_out
