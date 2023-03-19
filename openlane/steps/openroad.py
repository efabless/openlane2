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
import json
from decimal import Decimal
from base64 import b64encode
from abc import abstractmethod
from typing import List, Dict, Tuple, Optional

from .step import Step
from ..state import State
from .tclstep import TclStep
from ..state import DesignFormat
from .common_variables import (
    io_layer_variables,
    pdn_variables,
    rsz_variables,
    dpl_variables,
    routing_layer_variables,
    constraint_variables,
)

from ..logging import info, warn
from ..common import get_script_dir
from ..config import Variable, Path, StringEnum

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
            "STA_WRITE_LIB",
            bool,
            "Controls whether a timing model is written using OpenROAD OpenSTA after static timing analysis. This is an option as it in its current state, the timing model generation (and the model itself) can be quite buggy.",
            default=False,
        ),
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

    def run(
        self,
        **kwargs,
    ) -> State:
        """
        The `run()` override for the OpenROADStep class handles two things:

        1. Before the `super()` call: It creates a version of the liberty file
        minus cells that are known bad (i.e. those that fail DRC) and pass it on
        in the environment variable `LIB_PNR`.

        2. After the `super()` call: Processes the `or_metrics_out.json` file and
        updates the State's `metrics` property with any new metrics in that object.
        """
        kwargs, env = self.extract_env(kwargs)

        lib_pnr = self.toolbox.remove_cells_from_lib(
            frozenset(self.config["LIB"]),
            frozenset([self.config["BAD_CELL_LIST"]]),
            as_cell_lists=True,
        )

        env["LIB_PNR"] = lib_pnr

        state_out = super().run(env=env, **kwargs)

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

        assert isinstance(self.state_in, State)

        if self.state_out.get("def") == self.state_in.get("def"):
            return None

        if image := self.toolbox.render_png(self.config, str(self.state_out["def"])):
            image_encoded = b64encode(image).decode("utf8")
            return f'<img src="data:image/png;base64,{image_encoded}" />'

        return None


@Step.factory.register()
class NetlistSTA(OpenROADStep):
    id = "OpenROAD.NetlistSTA"
    name = "Netlist STA"
    long_name = "Netlist Static Timing Analysis"
    inputs = [DesignFormat.NETLIST, DesignFormat.SDC]
    outputs = []

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "sta.tcl")

    def run(self, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        env["RUN_STANDALONE"] = "1"
        env["STA_PRE_CTS"] = "1"
        return super().run(env=env, **kwargs)


@Step.factory.register()
class Floorplan(OpenROADStep):
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

    def run(self, **kwargs) -> State:
        path = self.config["FP_TRACKS_INFO"]
        tracks_info_str = open(path).read()
        tracks_commands = old_to_new_tracks(tracks_info_str)
        new_tracks_info = os.path.join(self.step_dir, "config.tracks")
        with open(new_tracks_info, "w") as f:
            f.write(tracks_commands)

        kwargs, env = self.extract_env(kwargs)
        env["TRACKS_INFO_FILE_PROCESSED"] = new_tracks_info
        return super().run(env=env, **kwargs)


@Step.factory.register()
class IOPlacement(OpenROADStep):
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
                "Points to the pin order configuration file to set the pins in specific directions (S, W, E, N). If not set, then the IO pins will be placed using OpenROAD's basic pin placer.",
            ),
        ]
    )

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "ioplacer.tcl")

    def run(self, **kwargs) -> State:
        if self.config["FP_PIN_ORDER_CFG"] is not None:
            # Skip - Step just checks and copies
            return Step.run(self, **kwargs)

        return super().run(**kwargs)


@Step.factory.register()
class TapDecapInsertion(OpenROADStep):
    id = "OpenROAD.TapDecapInsertion"
    name = "Tap/Decap Insertion"
    flow_control_variable = "RUN_TAP_DECAP_INSERTION"

    config_vars = OpenROADStep.config_vars + [
        Variable(
            "RUN_TAP_DECAP_INSERTION",
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
    id = "OpenROAD.GeneratePDN"
    name = "Generate PDN"
    long_name = "Power Distribution Network Generation"

    config_vars = OpenROADStep.config_vars + pdn_variables

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "pdn.tcl")


@Step.factory.register()
class GlobalPlacement(OpenROADStep):
    id = "OpenROAD.GlobalPlacement"
    name = "Global Placement"

    config_vars = (
        OpenROADStep.config_vars
        + routing_layer_variables
        + [
            Variable(
                "PL_TARGET_DENSITY_PCT",
                Optional[Decimal],
                "The desired placement density of cells. If not specified, the value will be equal to `FP_CORE_UTIL` + 5%.",
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
                "PL_ESTIMATE_PARASITICS",
                bool,
                "Specifies whether or not to run STA after global placement using OpenROAD's estimate_parasitics -placement and generate reports.",
                default=True,
            ),
        ]
    )

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "gpl.tcl")

    def run(self, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        env["PL_TARGET_DENSITY_PCT"] = f"{self.config['FP_CORE_UTIL'] + 5}"
        return super().run(env=env, **kwargs)


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
    id = "OpenROAD.DetailedPlacement"
    name = "Detailed Placement"

    config_vars = OpenROADStep.config_vars + dpl_variables

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "dpl.tcl")


@Step.factory.register()
class CTS(OpenROADStep):
    id = "OpenROAD.CTS"
    long_name = "Clock Tree Synthesis"
    flow_control_variable = "RUN_CTS"

    config_vars = dpl_variables + [
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
            "CTS_REPORT_TIMING",
            bool,
            "Specifies whether or not to run STA after clock tree synthesis using OpenROAD's `estimate_parasitics -placement`.",
            default=True,
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

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "cts.tcl")


@Step.factory.register()
class GlobalRouting(OpenROADStep):
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
                "GRT_REPAIR_ANTENNAE",
                bool,
                "Specifies the insertion strategy of diodes to be used in the flow.",
                default=True,
                deprecated_names=[("DIODE_INSERTION_STRATEGY", lambda x: x in [3, 6])],
            ),
            Variable(
                "GRT_ANTENNA_ITERS",
                int,
                "The maximum number of iterations for global antenna repairs.",
                default=3,
                deprecated_names=["GRT_ANT_ITERS"],
            ),
            Variable(
                "GRT_ESTIMATE_PARASITICS",
                bool,
                "Specifies whether or not to run STA after global routing using OpenROAD's `estimate_parasitics -global_routing`.",
                default=True,
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

    def run(self, **kwargs) -> State:
        state_out = super().run(**kwargs)

        antenna_rpt_path = os.path.join(self.step_dir, "antenna.rpt")
        antenna_rpt = open(antenna_rpt_path).read()
        nets = get_antenna_nets(antenna_rpt)

        antenna_report_post_fix_path = os.path.join(
            self.step_dir, "antenna_post_fix.rpt"
        )
        if os.path.exists(antenna_report_post_fix_path):
            net_count_before = len(nets)

            antenna_rpt = open(antenna_report_post_fix_path).read()
            nets = get_antenna_nets(antenna_rpt)
            net_count_after = len(nets)

            if net_count_before == net_count_after:
                info("Antenna count unchanged after OpenROAD antenna fixer.")
            elif net_count_after > net_count_before:
                warn(
                    "Inexplicably, the OpenROAD antenna fixer has generated more antenna. The flow may continue, but you may want to report a bug."
                )
            else:
                info(
                    f"Antenna count reduced using OpenROAD antenna fixer: {net_count_before} -> {net_count_after}"
                )

        state_out.metrics["antenna_nets"] = nets

        return state_out


@Step.factory.register()
class DetailedRouting(OpenROADStep):
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
            "Specifies the number of threads to be used in OpenROAD Detailed Routing. If unset, this will be equal to your thread count.",
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

    def run(self, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        if self.config.get("ROUTING_CORES") is None:
            env["ROUTING_CORES"] = str(os.cpu_count() or 1)
        return super().run(env=env, **kwargs)


@Step.factory.register()
class LayoutSTA(OpenROADStep):
    id = "OpenROAD.LayoutSTA"
    name = "Layout STA"
    long_name = "Layout Static Timing Analysis"
    inputs = [DesignFormat.ODB, DesignFormat.SDC]

    outputs = []

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "sta.tcl")

    def run(self, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        env["RUN_STANDALONE"] = "1"
        return super().run(env=env, **kwargs)


@Step.factory.register()
class FillInsertion(OpenROADStep):
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
class ParasiticsExtraction(OpenROADStep):
    id = "OpenROAD.ParasiticsExtraction"
    name = "Parasitics Extraction"
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
    ]

    # default inputs
    outputs = [DesignFormat.SPEF]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "rcx.tcl")

    def run(self, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        env["RCX_RULESET"] = f"{self.config['RCX_RULES']}"
        return super().run(env=env, **kwargs)


@Step.factory.register()
class ParasiticsSTA(OpenROADStep):
    id = "OpenROAD.ParasiticsSTA"
    name = "Parasitics STA"
    long_name = "Parasitics-based Static Timing Analysis"
    flow_control_variable = "RUN_SPEF_STA"

    config_vars = OpenROADStep.config_vars + [
        Variable(
            "RUN_SPEF_STA",
            bool,
            "Enables/disables this step.",
            default=True,
        ),
    ]

    inputs = OpenROADStep.inputs + [DesignFormat.SPEF]
    outputs = [DesignFormat.LIB, DesignFormat.SDF]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "sta.tcl")

    def run(self, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        env["RUN_STANDALONE"] = "1"
        return super().run(env=env, **kwargs)


# Antennae
def get_antenna_nets(report: str) -> List[str]:
    pattern = re.compile(r"Net:\s*(\w+)")
    antenna_nets = []

    for line in report.splitlines():
        m = pattern.match(line)
        if m is None:
            continue
        net = m[1]
        antenna_nets.append(net)

    return antenna_nets


@Step.factory.register()
class CheckAntennas(OpenROADStep):
    id = "OpenROAD.CheckAntennas"
    name = "Check Antennas"

    # default inputs
    outputs = []

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "check_antennas.tcl")

    def run(self, **kwargs) -> State:
        state_out = super().run(**kwargs)

        antenna_rpt = open(os.path.join(self.step_dir, "antenna.rpt")).read()

        state_out.metrics["antenna_nets"] = get_antenna_nets(antenna_rpt)

        return state_out


@Step.factory.register()
class IRDropReport(OpenROADStep):
    id = "OpenROAD.IRDropReport"
    name = "IR Drop Report"
    long_name = "Generate IR Drop Report"

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

    def run(self, **kwargs) -> State:
        from decimal import Decimal

        state_out = super().run(**kwargs)

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
                "Allows the creation of setup violations when fixing hold violations.",
                default=False,
            ),
        ]
    )

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "rsz_timing_postcts.tcl")


@Step.factory.register()
class ResizerTimingPostGRT(OpenROADStep):
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
