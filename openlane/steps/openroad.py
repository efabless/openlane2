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
import io
import os
import re
import json
import tempfile
import subprocess
from glob import glob
from decimal import Decimal
from base64 import b64encode
from abc import abstractmethod
from typing import List, Dict, Tuple, Optional
from concurrent.futures import Future, ThreadPoolExecutor

from .step import Step, StepException
from .tclstep import TclStep
from .common_variables import (
    io_layer_variables,
    pdn_variables,
    rsz_variables,
    dpl_variables,
    routing_layer_variables,
    constraint_variables,
)

from ..common import get_script_dir
from ..logging import err, info, warn
from ..config import Variable, StringEnum
from ..state import State, DesignFormat, Path

EXAMPLE_INPUT = """
li1 X 0.23 0.46
li1 Y 0.17 0.34
met1 X 0.17 0.34
met1 Y 0.17 0.34
met2 X 0.23 0.46
met2 Y 0.23 0.46
met3 X 0.34 0.68
met3 Y 0.34 0.68
met4 X 0.46 0.92
met4 Y 0.46 0.92
met5 X 1.70 3.40
met5 Y 1.70 3.40
"""


def old_to_new_tracks(old_tracks: str) -> str:
    """
    >>> old_to_new_tracks(EXAMPLE_INPUT)
    'make_tracks li1 -x_offset 0.23 -x_pitch 0.46 -y_offset 0.17 -y_pitch 0.34\\nmake_tracks met1 -x_offset 0.17 -x_pitch 0.34 -y_offset 0.17 -y_pitch 0.34\\nmake_tracks met2 -x_offset 0.23 -x_pitch 0.46 -y_offset 0.23 -y_pitch 0.46\\nmake_tracks met3 -x_offset 0.34 -x_pitch 0.68 -y_offset 0.34 -y_pitch 0.68\\nmake_tracks met4 -x_offset 0.46 -x_pitch 0.92 -y_offset 0.46 -y_pitch 0.92\\nmake_tracks met5 -x_offset 1.70 -x_pitch 3.40 -y_offset 1.70 -y_pitch 3.40\\n'
    """
    layers: Dict[str, Dict[str, Tuple[str, str]]] = {}

    for line in old_tracks.splitlines():
        if line.strip() == "":
            continue
        layer, cardinal, offset, pitch = line.split()
        layers[layer] = layers.get(layer) or {}
        layers[layer][cardinal] = (offset, pitch)

    final_str = ""
    for layer, data in layers.items():
        x_offset, x_pitch = data["X"]
        y_offset, y_pitch = data["Y"]
        final_str += f"make_tracks {layer} -x_offset {x_offset} -x_pitch {x_pitch} -y_offset {y_offset} -y_pitch {y_pitch}\n"

    return final_str


inf_rx = re.compile(r"\b(-?)inf\b")


class OpenROADStep(TclStep):
    inputs = [DesignFormat.ODB, DesignFormat.SDC]
    outputs = [
        DesignFormat.ODB,
        DesignFormat.DEF,
        DesignFormat.SDC,
        DesignFormat.NETLIST,
        DesignFormat.POWERED_NETLIST,
    ]

    config_vars = constraint_variables + [
        Variable(
            "PDN_CONNECT_MACROS_TO_GRID",
            bool,
            "Enables the connection of macros to the top level power grid.",
            default=True,
            deprecated_names=["FP_PDN_ENABLE_MACROS_GRID"],
        ),
        Variable(
            "PDN_MACRO_CONNECTIONS",
            Optional[List[str]],
            "Specifies explicit power connections of internal macros to the top level power grid, in the format: macro instance names, power domain vdd and ground net names, and macro vdd and ground pin names `<instance_name> <vdd_net> <gnd_net> <vdd_pin> <gnd_pin>`.",
            deprecated_names=["FP_PDN_MACRO_HOOKS"],
        ),
        Variable(
            "PDN_ENABLE_GLOBAL_CONNECTIONS",
            bool,
            "Enables the creation of global connections in PDN generation.",
            default=True,
            deprecated_names=["FP_PDN_ENABLE_GLOBAL_CONNECTIONS"],
        ),
    ]

    @abstractmethod
    def get_script_path(self):
        pass

    def prepare_env(self, env: dict, state: State) -> dict:
        env = super().prepare_env(env, state)

        lib_list = self.toolbox.filter_views(self.config, self.config["LIB"])
        lib_list += self.toolbox.get_macro_views(self.config, DesignFormat.LIB)

        lib_pnr = self.toolbox.remove_cells_from_lib(
            frozenset(lib_list),
            frozenset([self.config["PNR_EXCLUSION_CELL_LIST"]]),
            as_cell_lists=True,
        )

        env["PNR_LIBS"] = " ".join(lib_pnr)
        env["MACRO_LIBS"] = " ".join(
            [
                str(lib)
                for lib in self.toolbox.get_macro_views(self.config, DesignFormat.LIB)
            ]
        )

        return env

    def run(self, state_in, **kwargs) -> State:
        """
        The `run()` override for the OpenROADStep class handles two things:

        1. Before the `super()` call: It creates a version of the lib file
        minus cells that are known bad (i.e. those that fail DRC) and pass it on
        in the environment variable `PNR_LIBS`.

        2. After the `super()` call: Processes the `or_metrics_out.json` file and
        updates the State's `metrics` property with any new metrics in that object.
        """
        kwargs, env = self.extract_env(kwargs)

        state_out = super().run(state_in, env=env, **kwargs)

        metrics_path = os.path.join(self.step_dir, "or_metrics_out.json")
        if os.path.exists(metrics_path):
            metrics_str = open(metrics_path).read()
            metrics_str = inf_rx.sub(lambda m: f"{m[1] or ''}\"Infinity\"", metrics_str)
            new_metrics = json.loads(metrics_str)
            state_out.metrics.update(new_metrics)
        return state_out

    def get_command(self) -> List[str]:
        metrics_path = os.path.join(self.step_dir, "or_metrics_out.json")
        return ["openroad", "-exit", "-metrics", metrics_path, self.get_script_path()]

    def layout_preview(self) -> Optional[str]:
        if self.state_out is None:
            return None

        state_in = self.state_in.result()
        if self.state_out.get("def") == state_in.get("def"):
            return None

        if image := self.toolbox.render_png(self.config, str(self.state_out["def"])):
            image_encoded = b64encode(image).decode("utf8")
            return f'<img src="data:image/png;base64,{image_encoded}" />'

        return None


class STAStep(OpenROADStep):
    """
    Abstract class for an STA step
    """

    def layout_preview(self) -> Optional[str]:
        return None

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "sta", "multi_corner.tcl")


@Step.factory.register()
class STAMidPNR(STAStep):
    """
    Performs `Static Timing Analysis <https://en.wikipedia.org/wiki/Static_timing_analysis>`_
    using OpenROAD on an OpenROAD database, mid-PnR.
    """

    id = "OpenROAD.STAMidPNR"
    name = "STA (Mid-PnR)"
    long_name = "Static Timing Analysis (Mid-PnR)"

    inputs = [DesignFormat.ODB, DesignFormat.SDC]
    outputs = []


@Step.factory.register()
class STAPrePNR(STAStep):
    """
    Performs hierarchical `Static Timing Analysis <https://en.wikipedia.org/wiki/Static_timing_analysis>`_
    using OpenSTA on the pre-PnR Verilog netlist, with all available timing information
    for standard cells and macros for the default timing corner as specified in
    the ``DEFAULT_CORNER`` variable.

    If timing information is not available for macros, the macro in question
    will be black-boxed.
    """

    inputs = [DesignFormat.NETLIST, DesignFormat.SDC]
    outputs = []

    id = "OpenROAD.STAPrePNR"
    name = "STA (Pre-PnR)"
    long_name = "Static Timing Analysis"

    config_vars = STAStep.config_vars + [
        Variable(
            "STA_MACRO_PRIORITIZE_NL",
            bool,
            "Prioritize the use of Netlists + SPEF files over LIB files if available for Macros. Useful if extraction was done using OpenROAD, where SPEF files are far more accurate.",
            default=True,
        ),
    ]

    def get_command(self) -> List[str]:
        return ["sta", "-exit", self.get_script_path()]

    def run(self, state_in: State, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)

        timing_corner, timing_file_list = self.toolbox.get_timing_files(
            self.config,
            prioritize_nl=self.config["STA_MACRO_PRIORITIZE_NL"],
        )
        env["TIMING_CORNER_0"] = timing_corner
        for view in timing_file_list:
            env["TIMING_CORNER_0"] += f" {view}"

        env["OPENSTA"] = "1"

        return super().run(state_in, env=env, **kwargs)


@Step.factory.register()
class STAPostPNR(STAPrePNR):
    """
    Performs multi-corner `Static Timing Analysis <https://en.wikipedia.org/wiki/Static_timing_analysis>`_
    using OpenSTA on the post-PnR Verilog netlist, with extracted parasitics for
    both the top-level module and any associated macros.
    """

    id = "OpenROAD.STAPostPNR"
    name = "STA (Post-PnR)"
    long_name = "Static Timing Analysis (Post-PnR)"
    flow_control_variable = "RUN_MCSTA"

    inputs = STAPrePNR.inputs + [DesignFormat.SPEF]
    outputs = [DesignFormat.LIB, DesignFormat.SDF]

    config_vars = STAPrePNR.config_vars + [
        Variable(
            "RUN_MCSTA",
            bool,
            "Enables/disables this step.",
            default=True,
            deprecated_names=["RUN_SPEF_STA"],
        ),
    ]

    def run(self, state_in: State, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)

        env["LIB_SAVE_DIR"] = self.step_dir
        env["CURRENT_SPEF"] = ""
        env["OPENSTA"] = "1"
        for i, corner in enumerate(self.config["STA_CORNERS"]):
            if state_in["spef"] is None:
                raise StepException(
                    "SPEF extraction was not performed before parasitics STA."
                )

            if not isinstance(state_in["spef"], dict):
                raise StepException(
                    "Malformed input state: value for SPEF is not a dictionary."
                )

            spefs = self.toolbox.filter_views(self.config, state_in["spef"], corner)
            if len(spefs) < 1:
                raise StepException(
                    f"No SPEF file compatible with corner '{corner}' found."
                )
            elif len(spefs) > 1:
                warn(
                    f"Multiple SPEF files compatible with corner '{corner}' found. The first one encountered will be used."
                )
            spef = spefs[0]

            env["CURRENT_SPEF"] += f" {corner} {spef}"

            tc_key = f"TIMING_CORNER_{i}"
            _, timing_file_list = self.toolbox.get_timing_files(
                self.config,
                corner,
                prioritize_nl=self.config["STA_MACRO_PRIORITIZE_NL"],
            )
            timing_file_value = corner
            for view in timing_file_list:
                timing_file_value += f" {view}"
            env[tc_key] = timing_file_value

        state_out = super().run(state_in, env=env, **kwargs)

        lib_dict = state_out[DesignFormat.LIB] or {}

        if not isinstance(lib_dict, dict):
            raise StepException(
                "Malformed input state: value for LIB is not a dictionary."
            )
        libs = glob(os.path.join(self.step_dir, "*.lib"))
        for lib in libs:
            corner = lib[:-4]
            lib_dict[corner] = Path(os.path.join(self.step_dir, lib))

        state_out[DesignFormat.LIB] = lib_dict
        return state_out


@Step.factory.register()
class Floorplan(OpenROADStep):
    """
    Creates DEF and ODB files with the initial floorplan based on the Yosys netlist.
    """

    id = "OpenROAD.Floorplan"
    name = "Floorplan Init"
    long_name = "Floorplan Initialization"

    inputs = [DesignFormat.NETLIST, DesignFormat.SDC]

    config_vars = OpenROADStep.config_vars + [
        Variable(
            "FP_SIZING",
            StringEnum("FP_SIZING", ["relative", "absolute"]),
            "Whether to use relative sizing by making use of `FP_CORE_UTIL` or absolute one using `DIE_AREA`.",
            default="relative",
        ),
        Variable(
            "FP_ASPECT_RATIO",
            Decimal,
            "The core's aspect ratio (height / width).",
            default=1,
        ),
        Variable(
            "FP_CORE_UTIL",
            Decimal,
            "The core utilization percentage.",
            default=50,
            units="%",
        ),
        Variable(
            "CORE_AREA",
            Optional[str],
            'Specific core area (i.e. die area minus margins) to be used in floorplanning when `FP_SIZING` is set to `absolute`. Specified as a 4-corner rectangle "x0 y0 x1 y1".',
            units="μm",
        ),
        Variable(
            "BOTTOM_MARGIN_MULT",
            Decimal,
            "The core margin, in multiples of site heights, from the bottom boundary. If `FP_SIZING` is absolute and `CORE_AREA` is set, this variable has no effect.",
            default=4,
        ),
        Variable(
            "TOP_MARGIN_MULT",
            Decimal,
            "The core margin, in multiples of site heights, from the top boundary. If `FP_SIZING` is absolute and `CORE_AREA` is set, this variable has no effect.",
            default=4,
        ),
        Variable(
            "LEFT_MARGIN_MULT",
            Decimal,
            "The core margin, in multiples of site widths, from the left boundary. If `FP_SIZING` is absolute and `CORE_AREA` is set, this variable has no effect.",
            default=12,
        ),
        Variable(
            "RIGHT_MARGIN_MULT",
            Decimal,
            "The core margin, in multiples of site widths, from the right boundary. If `FP_SIZING` is absolute and `CORE_AREA` is set, this variable has no effect.",
            default=12,
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "floorplan.tcl")

    def run(self, state_in: State, **kwargs) -> State:
        path = self.config["FP_TRACKS_INFO"]
        tracks_info_str = open(path).read()
        tracks_commands = old_to_new_tracks(tracks_info_str)
        new_tracks_info = os.path.join(self.step_dir, "config.tracks")
        with open(new_tracks_info, "w") as f:
            f.write(tracks_commands)

        kwargs, env = self.extract_env(kwargs)
        env["TRACKS_INFO_FILE_PROCESSED"] = new_tracks_info
        return super().run(state_in, env=env, **kwargs)


@Step.factory.register()
class IOPlacement(OpenROADStep):
    """
    Places I/O pins on a floor-planned ODB file using OpenROAD's built-in placer.

    If ``FP_PIN_ORDER_CFG`` is not ``None``, this step is skipped (for
    compatibility with OpenLane 1.)
    """

    id = "OpenROAD.IOPlacement"
    name = "I/O Placement"

    config_vars = (
        OpenROADStep.config_vars
        + io_layer_variables
        + [
            Variable(
                "FP_IO_MODE",
                StringEnum("FP_IO_MODE", ["matching", "random_equidistant"]),
                "Decides the mode of the random IO placement option.",
                default="random_equidistant",
            ),
            Variable(
                "FP_IO_MIN_DISTANCE",
                Decimal,
                "The minimum distance between the IOs.",
                default=3,
                units="µm",
            ),
            Variable(
                "FP_PIN_ORDER_CFG",
                Optional[Path],
                "Path to a custom pin configuration file.",
            ),
        ]
    )

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "ioplacer.tcl")

    def run(self, state_in: State, **kwargs) -> State:
        if self.config["FP_PIN_ORDER_CFG"] is not None:
            # Skip - Step just checks and copies
            return Step.run(self, state_in, **kwargs)

        return super().run(state_in, **kwargs)


@Step.factory.register()
class TapEndcapInsertion(OpenROADStep):
    """
    Places well TAP cells across a floorplan, as well as end-cap cells at the
    edges of the floorplan.
    """

    id = "OpenROAD.TapEndcapInsertion"
    name = "Tap/Decap Insertion"
    flow_control_variable = "RUN_TAP_ENDCAP_INSERTION"

    config_vars = OpenROADStep.config_vars + [
        Variable(
            "RUN_TAP_ENDCAP_INSERTION",
            bool,
            "Enables/disables this step.",
            default=True,
            deprecated_names=["TAP_DECAP_INSERTION"],
        ),
        Variable(
            "FP_TAP_HORIZONTAL_HALO",
            Decimal,
            "Specify the horizontal halo size around macros during tap insertion.",
            default=10,
            units="µm",
        ),
        Variable(
            "FP_TAP_VERTICAL_HALO",
            Decimal,
            "Specify the vertical halo size around macros during tap insertion.",
            default="expr::$FP_TAP_HORIZONTAL_HALO",
            units="µm",
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "tapcell.tcl")


@Step.factory.register()
class GeneratePDN(OpenROADStep):
    """
    Creates a power distribution network on a floorplanned ODB file.
    """

    id = "OpenROAD.GeneratePDN"
    name = "Generate PDN"
    long_name = "Power Distribution Network Generation"

    config_vars = (
        OpenROADStep.config_vars
        + pdn_variables
        + [
            Variable(
                "PDN_CFG",
                Optional[Path],
                "A custom PDN configuration file. If not provided, the default PDN config will be used.",
            )
        ]
    )

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "pdn.tcl")


@Step.factory.register()
class GlobalPlacement(OpenROADStep):
    """
    Performs a somewhat nebulous initial placement for standard cells in a
    floorplan. While the placement is not concrete, it is enough to start
    accounting for issues such as fanout, transition time, et cetera.
    """

    id = "OpenROAD.GlobalPlacement"
    name = "Global Placement"

    config_vars = (
        OpenROADStep.config_vars
        + routing_layer_variables
        + [
            Variable(
                "PL_TARGET_DENSITY_PCT",
                Optional[Decimal],
                "The desired placement density of cells. If not specified, the value will be equal to (`FP_CORE_UTIL` + 5 * `GPL_CELL_PADDING` + 10).",
                units="%",
                deprecated_names=[
                    ("PL_TARGET_DENSITY", lambda d: Decimal(d) * Decimal(100.0))
                ],
            ),
            Variable(
                "PL_TIME_DRIVEN",
                bool,
                "Specifies whether the placer should use time driven placement.",
                default=True,
            ),
            Variable(
                "PL_SKIP_INITIAL_PLACEMENT",
                bool,
                "Specifies whether the placer should run initial placement or not.",
                default=False,
            ),
            Variable(
                "PL_ROUTABILITY_DRIVEN",
                bool,
                "Specifies whether the placer should use routability driven placement.",
                default=True,
            ),
            Variable(
                "FP_CORE_UTIL",
                Decimal,
                "The core utilization percentage.",
                default=50,
                units="%",
            ),
        ]
    )

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "gpl.tcl")

    def run(self, state_in: State, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        env[
            "PL_TARGET_DENSITY_PCT"
        ] = f"{self.config['FP_CORE_UTIL'] + (5 * self.config['GPL_CELL_PADDING']) + 10}"

        return super().run(state_in, env=env, **kwargs)


@Step.factory.register()
class BasicMacroPlacement(OpenROADStep):
    id = "OpenROAD.BasicMacroPlacement"
    name = "Basic Macro Placement"

    config_vars = OpenROADStep.config_vars + [
        Variable(
            "PL_MACRO_HALO",
            str,
            "Macro placement halo. Format: `{Horizontal} {Vertical}`.",
            default="0 0",
            units="μm",
        ),
        Variable(
            "PL_MACRO_CHANNEL",
            str,
            "Channel widths between macros. Format: `{Horizontal} {Vertical}`.",
            default="0 0",
            units="μm",
        ),
    ]

    def get_script_path(self):
        raise NotImplementedError()


@Step.factory.register()
class DetailedPlacement(OpenROADStep):
    """
    Performs "detailed placement" on an ODB file with global placement. This results
    in a concrete and legal placement of all cells.
    """

    id = "OpenROAD.DetailedPlacement"
    name = "Detailed Placement"

    config_vars = OpenROADStep.config_vars + dpl_variables

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "dpl.tcl")


@Step.factory.register()
class CTS(OpenROADStep):
    """
    Creates a `Clock tree <https://en.wikipedia.org/wiki/Clock_signal#Distribution>`_
    for an ODB file with detailed-placed cells, using reasonably accurate resistance
    and capacitance estimations. Detailed Placement is then re-performed to
    accomodate the new cells.
    """

    id = "OpenROAD.CTS"
    long_name = "Clock Tree Synthesis"
    flow_control_variable = "RUN_CTS"

    config_vars = (
        OpenROADStep.config_vars
        + dpl_variables
        + [
            Variable(
                "RUN_CTS",
                bool,
                "Enables/disables this step.",
                default=True,
                deprecated_names=["CLOCK_TREE_SYNTH"],
            ),
            Variable(
                "CTS_TARGET_SKEW",
                Decimal,
                "The target clock skew in picoseconds.",
                default=200,
                units="ps",
            ),
            Variable(
                "CTS_TOLERANCE",
                int,
                "An integer value that represents a tradeoff of QoR and runtime. Higher values will produce smaller runtime but worse QoR.",
                default=100,
            ),
            Variable(
                "CTS_SINK_CLUSTERING_SIZE",
                int,
                "Specifies the maximum number of sinks per cluster.",
                default=25,
            ),
            Variable(
                "CTS_SINK_CLUSTERING_MAX_DIAMETER",
                Decimal,
                "Specifies maximum diameter of the sink cluster.",
                default=50,
                units="μm",
            ),
            Variable(
                "CTS_CLK_MAX_WIRE_LENGTH",
                Decimal,
                "Specifies the maximum wire length on the clock net.",
                default=0,
                units="µm",
            ),
            Variable(
                "CTS_DISABLE_POST_PROCESSING",
                bool,
                "Specifies whether or not to disable post cts processing for outlier sinks.",
                default=False,
            ),
            Variable(
                "CTS_DISTANCE_BETWEEN_BUFFERS",
                Decimal,
                "Specifies the distance between buffers when creating the clock tree.",
                default=0,
                units="µm",
            ),
        ]
    )

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "cts.tcl")

    def run(self, state_in: State, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        if self.config.get("CLOCK_NET") is None:
            if clock_port := self.config["CLOCK_PORT"]:
                env["CLOCK_NET"] = " ".join(clock_port)
            else:
                warn(
                    "No CLOCK_NET (or CLOCK_PORT) specified. CTS cannot be performed. Returning state unaltered…"
                )
                return Step.run(self, state_in, **kwargs)

        state_out = super().run(state_in, env=env, **kwargs)
        state_out.metrics["cts__run"] = True
        return state_out


@Step.factory.register()
class GlobalRouting(OpenROADStep):
    """
    The initial phase of routing. Given a detailed-placed ODB file, this
    phase starts assigning coarse-grained routing "regions" for each net so they
    may be later connected to wires.

    Estimated capacitance and resistance values are much more accurate for
    global routing.

    Updates the ``antenna__count`` metric.

    At this stage, `antenna effect <https://en.wikipedia.org/wiki/Antenna_effect>`_
    mitigations may also be applied, updating the `antenna__count` count.
    See the variables for more info.
    """

    id = "OpenROAD.GlobalRouting"
    name = "Global Routing"

    config_vars = (
        OpenROADStep.config_vars
        + routing_layer_variables
        + [
            Variable(
                "DIODE_PADDING",
                int,
                "Diode cell padding; increases the width of diode cells during placement checks..",
                default=2,
                units="sites",
            ),
            Variable(
                "GRT_ALLOW_CONGESTION",
                bool,
                "Allow congestion during global routing",
                default=False,
            ),
            Variable(
                "GRT_REPAIR_ANTENNAS",
                bool,
                "Specifies the insertion strategy of diodes to be used in the flow.",
                default=True,
            ),
            Variable(
                "GRT_ANTENNA_ITERS",
                int,
                "The maximum number of iterations for global antenna repairs.",
                default=3,
                deprecated_names=["GRT_ANT_ITERS"],
            ),
            Variable(
                "GRT_OVERFLOW_ITERS",
                int,
                "The maximum number of iterations waiting for the overflow to reach the desired value.",
                default=50,
            ),
        ]
    )

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "grt.tcl")

    def run(self, state_in: State, **kwargs) -> State:
        state_out = super().run(state_in, **kwargs)

        antenna_rpt_path = os.path.join(self.step_dir, "antenna.rpt")
        net_count = get_antenna_nets(
            open(antenna_rpt_path),
            open(os.path.join(self.step_dir, "antenna_nets.txt"), "w"),
        )

        antenna_report_post_fix_path = os.path.join(
            self.step_dir, "antenna_post_fix.rpt"
        )
        if os.path.exists(antenna_report_post_fix_path):
            net_count_after = get_antenna_nets(
                open(antenna_report_post_fix_path),
                open(os.path.join(self.step_dir, "antenna_nets_post_fix.txt"), "w"),
            )

            if net_count == net_count_after:
                info(
                    f"Antenna count unchanged after OpenROAD antenna fixer. ({net_count})"
                )
            elif net_count_after > net_count:
                warn(
                    f"Inexplicably, the OpenROAD antenna fixer has generated more antennas ({net_count} -> {net_count_after}). The flow will continue, but you may want to report a bug."
                )
            else:
                info(
                    f"Antenna count reduced using OpenROAD antenna fixer: {net_count} -> {net_count_after}"
                )
            net_count = net_count_after

        state_out.metrics["antenna__count"] = net_count

        return state_out


@Step.factory.register()
class DetailedRouting(OpenROADStep):
    """
    The latter phase of routing. This transforms the abstract nets from global
    routing into wires on the metal layers that respect all design rules, avoids
    creating accidental shorts, and ensures all wires are connected.

    This is by far the longest part of a typical flow, taking hours, days or weeks
    on larger designs.

    After this point, all cells connected to a net can no longer be moved or
    removed without a custom-written step of some kind that will also rip up
    wires.
    """

    id = "OpenROAD.DetailedRouting"
    name = "Detailed Routing"
    flow_control_variable = "RUN_DRT"

    config_vars = OpenROADStep.config_vars + [
        Variable(
            "RUN_DRT",
            bool,
            "Enables/disables this step.",
            default=True,
        ),
        Variable(
            "ROUTING_CORES",
            Optional[int],
            "Specifies the number of threads to be used in OpenROAD Detailed Routing. If unset, this will be equal to your machine's thread count.",
        ),
        Variable(
            "DRT_MIN_LAYER",
            Optional[str],
            "An optional override to the lowest layer used in detailed routing. For example, in sky130, you may want global routing to avoid li1, but let detailed routing use li1 if it has to.",
        ),
        Variable(
            "DRT_MAX_LAYER",
            Optional[str],
            "An optional override to the highest layer used in detailed routing.",
        ),
        Variable(
            "DRT_OPT_ITERS",
            int,
            "Specifies the maximum number of optimization iterations during Detailed Routing in TritonRoute.",
            default=64,
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "drt.tcl")

    def run(self, state_in: State, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        if self.config.get("ROUTING_CORES") is None:
            env["ROUTING_CORES"] = str(os.cpu_count() or 1)
        return super().run(state_in, env=env, **kwargs)


@Step.factory.register()
class LayoutSTA(OpenROADStep):
    """
    Performs `Static Timing Analysis <https://en.wikipedia.org/wiki/Static_timing_analysis>`_
    using OpenROAD on the ODB layout in its current state.
    """

    id = "OpenROAD.LayoutSTA"
    name = "Layout STA"
    long_name = "Layout Static Timing Analysis"
    inputs = [DesignFormat.ODB, DesignFormat.SDC]

    outputs = []

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "sta.tcl")

    def run(self, state_in: State, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        env["RUN_STANDALONE"] = "1"
        return super().run(state_in, env=env, **kwargs)


@Step.factory.register()
class FillInsertion(OpenROADStep):
    """
    Fills gaps in the floorplan with filler and decapacitance cells.

    This is run after detailed placement. After this point, the design is basically
    completely hardened.
    """

    id = "OpenROAD.FillInsertion"
    name = "Fill Insertion"
    flow_control_variable = "RUN_FILL_INSERTION"

    config_vars = OpenROADStep.config_vars + [
        Variable(
            "RUN_FILL_INSERTION",
            bool,
            "Enables/disables this step.",
            default=True,
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "fill.tcl")


@Step.factory.register()
class RCX(OpenROADStep):
    """
    This extracts `parasitic <https://en.wikipedia.org/wiki/Parasitic_element_(electrical_networks)>`_
    electrical values from a detailed-placed circuit. These can be used to create
    basically the highest accurate STA possible for a design.
    """

    id = "OpenROAD.RCX"
    name = "Parasitics (RC) Extraction"
    long_name = "Parasitic Resistance/Capacitance Extraction"
    flow_control_variable = "RUN_SPEF_EXTRACTION"

    config_vars = OpenROADStep.config_vars + [
        Variable(
            "RUN_SPEF_EXTRACTION",
            bool,
            "Enables/disables this step.",
            default=True,
        ),
        Variable(
            "RCX_MERGE_VIA_WIRE_RES",
            bool,
            "If enabled, the via and wire resistances will be merged.",
            default=True,
        ),
        Variable(
            "RCX_SDC_FILE",
            Optional[Path],
            "Specifies SDC file to be used for RCX-based STA, which can be different from the one used for implementation.",
        ),
        Variable(
            "RCX_CORES",
            Optional[int],
            "Specifies the number of processes to be used during Multi-Corner RCX. If unset or zero, this will be equal to your machine's thread count.",
        ),
    ]

    inputs = [DesignFormat.DEF]
    outputs = [DesignFormat.SPEF]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "rcx.tcl")

    def run(self, state_in: State, **kwargs) -> State:
        process_count = os.cpu_count()
        if cores := self.config.get("RCX_CORES"):
            process_count = cores

        state = Step.run(self, state_in, **kwargs)
        kwargs, env = self.extract_env(kwargs)
        env = self.prepare_env(env, state)

        def run_corner(corner: str):
            rcx_ruleset = self.config["RCX_RULESETS"].get(corner)
            if rcx_ruleset is None:
                warn(
                    f"RCX ruleset for corner {corner} not found. The corner may be ill-defined."
                )
                return None

            corner_clean = corner
            if corner_clean.endswith("_*"):
                corner_clean = corner_clean[:-2]

            nonlocal env
            current_env = env.copy()

            tech_lefs = self.toolbox.filter_views(
                self.config, self.config["TECH_LEFS"], corner
            )
            if len(tech_lefs) < 1:
                warn(f"No tech lef for timing corner {corner} found.")
                return None
            elif len(tech_lefs) > 1:
                warn(
                    f"Multiple tech lefs found for timing corner {corner}. Only the first one matched will be used."
                )

            current_env["RCX_LEF"] = tech_lefs[0]
            current_env["RCX_RULESET"] = rcx_ruleset

            out = os.path.join(
                self.step_dir, f"{self.config['DESIGN_NAME']}.{corner_clean}.spef"
            )
            current_env["SAVE_SPEF"] = out

            log_path = os.path.join(self.step_dir, f"{corner_clean}.log")
            info(
                f"Running RCX for the {corner_clean} interconnect corner ({log_path})…"
            )

            try:
                self.run_subprocess(
                    self.get_command(),
                    log_to=log_path,
                    env=current_env,
                    silent=True,
                )
                info(f"Finished RCX for the {corner_clean} interconnect corner.")
            except subprocess.CalledProcessError as e:
                err(f"Failed RCX for the {corner_clean} interconnect corner:")
                raise e

            return out

        futures: Dict[str, Future[str]] = {}
        with ThreadPoolExecutor(process_count) as tpe:
            for corner in self.config["RCX_RULESETS"]:
                futures[corner] = tpe.submit(
                    run_corner,
                    corner,
                )

        spef_dict = state[DesignFormat.SPEF] or {}
        if not isinstance(spef_dict, dict):
            raise StepException(
                "Malformed input state: value for SPEF is not a dictionary."
            )

        for corner, future in futures.items():
            if result := future.result():
                spef_dict[corner] = Path(result)

        state[DesignFormat.SPEF] = spef_dict

        return state


# Antennas
def get_antenna_nets(report: io.TextIOWrapper, output: io.TextIOWrapper) -> int:
    pattern = re.compile(r"Net:\s*(\w+)")
    count = 0

    for line in report:
        line = line.strip()
        m = pattern.match(line)
        if m is None:
            continue
        net = m[1]
        output.write(f"{net}\n")
        count += 1

    return count


@Step.factory.register()
class CheckAntennas(OpenROADStep):
    """
    Runs OpenROAD to check if one or more long nets may constitute an
    `antenna risk <https://en.wikipedia.org/wiki/Antenna_effect>`_.

    The metric ``antenna__count`` will be updated with the number of violating nets.
    """

    id = "OpenROAD.CheckAntennas"
    name = "Check Antennas"

    # default inputs
    outputs = []

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "check_antennas.tcl")

    def run(self, state_in: State, **kwargs) -> State:
        state_out = super().run(state_in, **kwargs)

        state_out.metrics["antenna__count"] = get_antenna_nets(
            open(os.path.join(self.step_dir, "antenna.rpt")),
            open(os.path.join(self.step_dir, "antenna_net_list.txt"), "w"),
        )

        return state_out


@Step.factory.register()
class IRDropReport(OpenROADStep):
    """
    Performs voltage-drop analysis on the power distribution network.
    """

    id = "OpenROAD.IRDropReport"
    name = "IR Drop Report"
    long_name = "Generate IR Drop Report"
    flow_control_variable = "RUN_IRDROP_REPORT"

    inputs = [DesignFormat.ODB, DesignFormat.SPEF]
    outputs = []

    config_vars = OpenROADStep.config_vars + [
        Variable(
            "RUN_IRDROP_REPORT",
            bool,
            "Enables/disables this step.",
            default=True,
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "irdrop.tcl")

    def run(self, state_in: State, **kwargs) -> State:
        from decimal import Decimal

        if state_in["spef"] is None:
            raise StepException(
                "SPEF extraction was not performed before IR drop report."
            )

        if not isinstance(state_in["spef"], dict):
            raise StepException(
                "Malformed input state: value for SPEF is not a dictionary."
            )

        kwargs, env = self.extract_env(kwargs)

        spefs_in = self.toolbox.filter_views(self.config, state_in["spef"])
        if len(spefs_in) > 1:
            raise StepException(
                "Found more than one input SPEF file for the default corner."
            )
        elif len(spefs_in) < 1:
            raise StepException("No SPEF file found for the default corner.")

        env["CURRENT_SPEF"] = str(spefs_in[0])
        state_out = super().run(state_in, env=env, **kwargs)

        report = open(os.path.join(self.step_dir, "irdrop.rpt")).read()

        voltage_rx = re.compile(r"Worstcase voltage\s*:\s*([\d\.\+\-e]+)\s*V")
        avg_drop_rx = re.compile(r"Average IR drop\s*:\s*([\d\.\+\-e]+)\s*V")
        worst_drop_rx = re.compile(r"Worstcase IR drop\s*:\s*([\d\.\+\-e]+)\s*V")

        if m := voltage_rx.search(report):
            value_float = float(m[1])
            value_dec = Decimal(value_float)
            state_out.metrics["ir__voltage__worst"] = value_dec
        else:
            raise Exception(
                "OpenROAD IR Drop Log format has changed- please file an issue."
            )

        if m := avg_drop_rx.search(report):
            value_float = float(m[1])
            value_dec = Decimal(value_float)
            state_out.metrics["ir__drop__avg"] = value_dec
        else:
            raise Exception(
                "OpenROAD IR Drop Log format has changed- please file an issue."
            )

        if m := worst_drop_rx.search(report):
            value_float = float(m[1])
            value_dec = Decimal(value_float)
            state_out.metrics["ir__drop__worst"] = value_dec
        else:
            raise Exception(
                "OpenROAD IR Drop Log format has changed- please file an issue."
            )

        return state_out


# Resizer Steps


@Step.factory.register()
class RepairDesign(OpenROADStep):
    """
    Runs a number of design "repairs" on a global-placed ODB file.
    """

    id = "OpenROAD.RepairDesign"
    name = "Repair Design (Post-Global Placement)"
    flow_control_variable = "RUN_REPAIR_DESIGN"

    config_vars = (
        OpenROADStep.config_vars
        + rsz_variables
        + [
            Variable(
                "RUN_REPAIR_DESIGN",
                bool,
                "Enables/disables this step.",
                default=True,
                deprecated_names=["PL_RESIZER_DESIGN_OPTIMIZATIONS"],
            ),
            Variable(
                "DESIGN_REPAIR_BUFFER_INPUT_PORTS",
                bool,
                "Specifies whether or not to insert buffers on input ports when design repairs are run.",
                default=True,
                deprecated_names=["PL_RESIZER_BUFFER_INPUT_PORTS"],
            ),
            Variable(
                "DESIGN_REPAIR_BUFFER_OUTPUT_PORTS",
                bool,
                "Specifies whether or not to insert buffers on input ports when design repairs are run.",
                default=True,
                deprecated_names=["PL_RESIZER_BUFFER_OUTPUT_PORTS"],
            ),
            Variable(
                "DESIGN_REPAIR_TIE_FANOUT",
                bool,
                "Specifies whether or not to repair tie cells fanout when design repairs are run.",
                default=True,
                deprecated_names=["PL_RESIZER_REPAIR_TIE_FANOUT"],
            ),
            Variable(
                "DESIGN_REPAIR_TIE_SEPARATION",
                bool,
                "Allows tie separation when performing design repairs.",
                default=False,
                deprecated_names=["PL_RESIZER_TIE_SEPERATION"],
            ),
            Variable(
                "DESIGN_REPAIR_MAX_WIRE_LENGTH",
                Decimal,
                "Specifies the maximum wire length cap used by resizer to insert buffers. If set to 0, no buffers will be inserted.",
                default=0,
                units="µm",
                deprecated_names=["PL_RESIZER_MAX_WIRE_LENGTH"],
            ),
            Variable(
                "DESIGN_REPAIR_MAX_SLEW_PCT",
                Decimal,
                "Specifies a margin for the slews during design repair.",
                default=20,
                units="%",
                deprecated_names=["PL_RESIZER_MAX_SLEW_MARGIN"],
            ),
            Variable(
                "DESIGN_REPAIR_MAX_CAP_PCT",
                Decimal,
                "Specifies a margin for the capacitances during design repair.",
                default=20,
                units="%",
                deprecated_names=["PL_RESIZER_MAX_CAP_MARGIN"],
            ),
        ]
    )

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "repair_design.tcl")


@Step.factory.register()
class ResizerTimingPostCTS(OpenROADStep):
    """
    First attempt to meet timing requirements for a cell based on basic timing
    information after clock tree synthesis.

    Standard cells may be resized, and buffer cells may be inserted to ensure
    that no hold violations exist and no setup violations exist at the current
    clock.
    """

    id = "OpenROAD.ResizerTimingPostCTS"
    name = "Resizer Timing Optimizations (Post-Clock Tree Synthesis)"
    flow_control_variable = "RUN_POST_CTS_RESIZER_TIMING"

    config_vars = (
        OpenROADStep.config_vars
        + rsz_variables
        + [
            Variable(
                "RUN_POST_CTS_RESIZER_TIMING",
                bool,
                "Enables/disables this step.",
                default=True,
                deprecated_names=["PL_RESIZER_TIMING_OPTIMIZATIONS"],
            ),
            Variable(
                "PL_RESIZER_HOLD_SLACK_MARGIN",
                Decimal,
                "Specifies a time margin for the slack when fixing hold violations. Normally the resizer will stop when it reaches zero slack. This option allows you to overfix.",
                default=0.1,
                units="ns",
            ),
            Variable(
                "PL_RESIZER_SETUP_SLACK_MARGIN",
                Decimal,
                "Specifies a time margin for the slack when fixing setup violations.",
                default=0.05,
                units="ns",
            ),
            Variable(
                "PL_RESIZER_HOLD_MAX_BUFFER_PCT",
                Decimal,
                "Specifies a max number of buffers to insert to fix hold violations. This number is calculated as a percentage of the number of instances in the design.",
                default=50,
                deprecated_names=["PL_RESIZER_HOLD_MAX_BUFFER_PERCENT"],
            ),
            Variable(
                "PL_RESIZER_SETUP_MAX_BUFFER_PCT",
                Decimal,
                "Specifies a max number of buffers to insert to fix setup violations. This number is calculated as a percentage of the number of instances in the design.",
                default=50,
                units="%",
                deprecated_names=["PL_RESIZER_SETUP_MAX_BUFFER_PERCENT"],
            ),
            Variable(
                "PL_RESIZER_ALLOW_SETUP_VIOS",
                bool,
                "Allows the creation of setup violations when fixing hold violations. Setup violations are less dangerous as they simply mean a chip may not run at its rated speed, however, chips with hold violations are essentially dead-on-arrival.",
                default=False,
            ),
        ]
    )

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "rsz_timing_postcts.tcl")


@Step.factory.register()
class ResizerTimingPostGRT(OpenROADStep):
    """
    Second attempt to meet timing requirements for a cell based on timing
    information after estimating resistance and capacitance values based on
    global routing.

    Standard cells may be resized, and buffer cells may be inserted to ensure
    that no hold violations exist and no setup violations exist at the current
    clock.
    """

    id = "OpenROAD.ResizerTimingPostGRT"
    name = "Resizer Timing Optimizations (Post-Global Routing)"
    flow_control_variable = "RUN_POST_GRT_RESIZER_TIMING"

    config_vars = (
        OpenROADStep.config_vars
        + rsz_variables
        + [
            Variable(
                "RUN_POST_GRT_RESIZER_TIMING",
                bool,
                "Enables/disables this step.",
                default=True,
                deprecated_names=["GLB_RESIZER_TIMING_OPTIMIZATIONS"],
            ),
            Variable(
                "GRT_RESIZER_HOLD_SLACK_MARGIN",
                str,
                "Specifies a time margin for the slack when fixing hold violations. Normally the resizer will stop when it reaches zero slack. This option allows you to overfix.",
                default=0.05,
                units="ns",
                deprecated_names=["GLB_RESIZER_HOLD_SLACK_MARGIN"],
            ),
            Variable(
                "GRT_RESIZER_SETUP_SLACK_MARGIN",
                str,
                "Specifies a time margin for the slack when fixing setup violations.",
                default=0.025,
                units="ns",
                deprecated_names=["GLB_RESIZER_SETUP_SLACK_MARGIN"],
            ),
            Variable(
                "GRT_RESIZER_HOLD_MAX_BUFFER_PCT",
                Decimal,
                "Specifies a max number of buffers to insert to fix hold violations. This number is calculated as a percentage of the number of instances in the design.",
                default=50,
                units="%",
                deprecated_names=["GLB_RESIZER_HOLD_MAX_BUFFER_PERCENT"],
            ),
            Variable(
                "GRT_RESIZER_SETUP_MAX_BUFFER_PCT",
                Decimal,
                "Specifies a max number of buffers to insert to fix setup violations. This number is calculated as a percentage of the number of instances in the design.",
                default=50,
                units="%",
                deprecated_names=["GLB_RESIZER_SETUP_MAX_BUFFER_PERCENT"],
            ),
            Variable(
                "GRT_RESIZER_ALLOW_SETUP_VIOS",
                bool,
                "Allows setup violations when fixing hold.",
                default=False,
                deprecated_names=["GLB_RESIZER_ALLOW_SETUP_VIOS"],
            ),
        ]
    )

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "rsz_timing_postgrt.tcl")


@Step.factory.register()
class OpenGUI(Step):
    """
    Opens the ODB view in the OpenROAD GUI. Useful to inspect some parameters,
    such as routing density and whatnot.
    """

    id = "OpenROAD.OpenGUI"
    name = "Open In GUI"

    inputs = [DesignFormat.ODB]
    outputs = []

    def run(self, state_in: State, **kwargs) -> State:
        state_out = super().run(state_in, **kwargs)

        with tempfile.NamedTemporaryFile("a+", suffix=".tcl") as f:
            f.write(f"read_db \"{state_out['odb']}\"")
            f.flush()

            subprocess.check_call(
                [
                    "openroad",
                    "-no_splash",
                    "-gui",
                    f.name,
                ]
            )

        return state_out
