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
import re
import io
import json
from abc import abstractmethod
from typing import List, Optional, Tuple

from .tclstep import TclStep
from .step import ViewsUpdate, MetricsUpdate, Step
from .common_variables import constraint_variables

from ..config import Variable
from ..logging import debug, verbose
from ..state import State, DesignFormat, Path
from ..common import get_script_dir, StringEnum

starts_with_whitespace = re.compile(r"^\s+.+$")


def parse_yosys_check(
    report: io.TextIOBase,
    tristate_okay: bool = False,
) -> int:
    verbose("Parsing synthesis checks…")
    errors_encountered: int = 0
    current_warning = None

    for line in report:
        if line.startswith("Warning:") or line.startswith("Found and reported"):
            if current_warning is not None:
                if tristate_okay and "tribuf" in current_warning:
                    debug("Ignoring tristate-related error:")
                    debug(current_warning)
                else:
                    debug("Encountered check error:")
                    debug(current_warning)
                    errors_encountered += 1
            current_warning = line
        elif (
            starts_with_whitespace.match(line) is not None
            and current_warning is not None
        ):
            current_warning += line
        else:
            pass
    return errors_encountered


class YosysStep(TclStep):
    reproducibles_allowed = False

    config_vars = [
        Variable(
            "VERILOG_FILES",
            List[Path],
            "The paths of the design's Verilog files.",
        ),
        Variable(
            "SYNTH_DEFINES",
            Optional[List[str]],
            "Synthesis defines",
        ),
        Variable(
            "VERILOG_INCLUDE_DIRS",
            Optional[List[str]],
            "Specifies the Verilog `include` directories.",
        ),
        Variable(
            "SYNTH_READ_BLACKBOX_LIB",
            bool,
            "Additionally read the liberty file(s) as a blackbox. This will allow RTL designs to incorporate explicitly declared standard cells that will not be tech-mapped or reinterpreted.",
            default=False,
        ),
    ]

    def get_command(self) -> List[str]:
        script_path = self.get_script_path()
        return ["yosys", "-c", script_path]

    @abstractmethod
    def get_script_path(self) -> str:
        pass

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        kwargs, env = self.extract_env(kwargs)

        lib_list = self.toolbox.filter_views(self.config, self.config["LIB"])
        lib_synth = self.toolbox.remove_cells_from_lib(
            frozenset(lib_list),
            excluded_cells=frozenset(
                [
                    self.config["SYNTH_EXCLUSION_CELL_LIST"],
                    self.config["PNR_EXCLUSION_CELL_LIST"],
                ]
            ),
            as_cell_lists=True,
        )

        env["SYNTH_LIBS"] = " ".join(lib_synth)

        macro_libs = self.toolbox.get_macro_views(
            self.config,
            DesignFormat.LIB,
        )
        if len(macro_libs) != 0:
            env["MACRO_LIBS"] = " ".join([str(lib) for lib in macro_libs])

        macro_nls = self.toolbox.get_macro_views(
            self.config,
            DesignFormat.NETLIST,
            unless_exist=DesignFormat.LIB,
        )
        if len(macro_nls) != 0:
            env["MACRO_NLS"] = " ".join([str(nl) for nl in macro_nls])

        return super().run(state_in, env=env, **kwargs)


@Step.factory.register()
class JsonHeader(YosysStep):
    id = "Yosys.JsonHeader"
    inputs = []
    outputs = [DesignFormat.JSON_HEADER]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "yosys", "json_header.tcl")

    config_vars = YosysStep.config_vars + [
        Variable(
            "SYNTH_POWER_DEFINE",
            Optional[str],
            "Specifies the name of the define used to guard power and ground connections",
            deprecated_names=["SYNTH_USE_PG_PINS_DEFINES"],
        ),
    ]


@Step.factory.register()
class Synthesis(YosysStep):
    """
    Performs synthesis and technology mapping using Yosys and ABC, emitting a
    netlist. Requires Yosys 0.26 or higher.

    Some metrics will also be extracted and updated, namely:

    * ``design__instance__count``
    * ``design__instance_unmapped__count``

    If using Yosys 0.27 or higher:

    * ``design__instance__area`` is also updated.
    """

    id = "Yosys.Synthesis"
    inputs = []  # The input RTL is part of the configuration
    outputs = [DesignFormat.NETLIST]

    config_vars = (
        YosysStep.config_vars
        + constraint_variables
        + [
            Variable(
                "SYNTH_CHECKS_ALLOW_TRISTATE",
                bool,
                "Ignore multiple-driver warnings if they are connected to tri-state buffers on a best-effort basis.",
                default=True,
            ),
            Variable(
                "SYNTH_AUTONAME",
                bool,
                "Generates names for netlist instances. This results in instance names that can be extremely long, but are more human-readable.",
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
                "SYNTH_ABC_BUFFERING",
                bool,
                "Enables `abc` cell buffering.",
                default=True,
                deprecated_names=["SYNTH_BUFFERING"],
            ),
            Variable(
                "SYNTH_DIRECT_WIRE_BUFFERING",
                bool,
                "Enables inserting buffer cells for directly connected wires.",
                default=True,
                deprecated_names=["SYNTH_BUFFER_DIRECT_WIRES"],
            ),
            Variable(
                "SYNTH_SPLITNETS",
                bool,
                "Splits multi-bit nets into single-bit nets. Easier to trace but may not be supported by all tools.",
                default=True,
            ),
            Variable(
                "SYNTH_SIZING",
                bool,
                "Enables `abc` cell sizing (instead of buffering).",
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
                "SYNTH_ELABORATE_FLATTEN",
                bool,
                "If `SYNTH_ELABORATE_ONLY` is specified, this variable controls whether or not the top level should be flattened.",
                default=True,
                deprecated_names=["SYNTH_FLAT_TOP"],
            ),
        ]
    )

    def get_script_path(self):
        return os.path.join(get_script_dir(), "yosys", "synthesize.tcl")

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        views_updates, metric_updates = super().run(state_in, **kwargs)

        stats_file = os.path.join(self.step_dir, "reports", "stat.json")
        stats_str = open(stats_file).read()
        stats = json.loads(stats_str)

        metric_updates = {}
        metric_updates["design__instance__count"] = stats["design"]["num_cells"]
        if chip_area := stats["design"].get("area"):  # needs nonzero area
            metric_updates["design__instance__area"] = chip_area

        cells = stats["design"]["num_cells_by_type"]
        unmapped_keyword = "$"
        unmapped_cells = [
            cells[y] for y in cells.keys() if y.startswith(unmapped_keyword)
        ]
        metric_updates["design__instance_unmapped__count"] = sum(unmapped_cells)

        check_error_count_file = os.path.join(
            self.step_dir, "reports", "pre_synth_chk.rpt"
        )
        metric_updates["synthesis__check_error__count"] = 0
        if os.path.exists(check_error_count_file):
            metric_updates["synthesis__check_error__count"] = parse_yosys_check(
                open(check_error_count_file),
                self.config["SYNTH_CHECKS_ALLOW_TRISTATE"],
            )

        return views_updates, metric_updates
