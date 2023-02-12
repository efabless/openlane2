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
from abc import abstractmethod
from typing import List, Dict, Tuple

from .step import Step
from .tclstep import TclStep
from .state import State
from .design_format import DesignFormat
from ..common import get_script_dir, log, warn

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
    inputs = [DesignFormat.ODB]
    outputs = [
        DesignFormat.ODB,
        DesignFormat.DEF,
        DesignFormat.SDC,
        DesignFormat.NETLIST,
        DesignFormat.POWERED_NETLIST,
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

        2. After the `super()` call: Processes the `metrics.json` file and
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

        metrics_path = os.path.join(self.step_dir, "metrics.json")
        if os.path.exists(metrics_path):
            metrics_str = open(metrics_path).read()
            metrics_str = inf_rx.sub(lambda m: f"{m[1] or ''}\"Infinity\"", metrics_str)
            new_metrics = json.loads(metrics_str)
            state_out.metrics.update(new_metrics)
        return state_out

    def get_command(self) -> List[str]:
        metrics_path = os.path.join(self.step_dir, "metrics.json")
        return ["openroad", "-exit", "-metrics", metrics_path, self.get_script_path()]


@Step.factory.register("OpenROAD.NetlistSTA")
class NetlistSTA(OpenROADStep):
    name = "Netlist STA"
    long_name = "Netlist Static Timing Analysis"
    inputs = [DesignFormat.NETLIST]
    outputs = []

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "sta.tcl")

    def run(self, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        env["RUN_STANDALONE"] = "1"
        env["STA_PRE_CTS"] = "1"
        return super().run(env=env, **kwargs)


@Step.factory.register("OpenROAD.Floorplan")
class Floorplan(OpenROADStep):
    name = "Floorplan Init"
    long_name = "Floorplan Initialization"

    inputs = [DesignFormat.NETLIST]

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


@Step.factory.register("OpenROAD.IOPlacement")
class IOPlacement(OpenROADStep):
    id = "io-placement"
    name = "I/O Placement"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "ioplacer.tcl")

    def run(self, **kwargs) -> State:
        if self.config["FP_PIN_ORDER_CFG"] is not None:
            # Skip - Step just checks and copies
            return Step.run(self, **kwargs)

        return super().run(**kwargs)


@Step.factory.register("OpenROAD.TapDecapInsertion")
class TapDecapInsertion(OpenROADStep):
    id = "tap-decap-insertion"
    name = "Tap/Decap Insertion"
    flow_control_variable = "RUN_TAP_DECAP_INSERTION"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "tapcell.tcl")


@Step.factory.register("OpenROAD.GeneratePDN")
class GeneratePDN(OpenROADStep):
    name = "Generate PDN"
    long_name = "Power Distribution Network Generation"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "pdn.tcl")


@Step.factory.register("OpenROAD.GlobalPlacement")
class GlobalPlacement(OpenROADStep):
    name = "Global Placement"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "gpl.tcl")

    def run(self, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        env["PL_TARGET_DENSITY"] = f"{self.config['FP_CORE_UTIL'] + 5}"
        return super().run(env=env, **kwargs)


@Step.factory.register("OpenROAD.DetailedPlacement")
class DetailedPlacement(OpenROADStep):
    name = "Detailed Placement"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "dpl.tcl")


@Step.factory.register("OpenROAD.CTS")
class CTS(OpenROADStep):
    long_name = "Clock Tree Synthesis"
    flow_control_variable = "RUN_CTS"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "cts.tcl")


@Step.factory.register("OpenROAD.GlobalRouting")
class GlobalRouting(OpenROADStep):
    name = "Global Routing"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "grt.tcl")

    def run(self, **kwargs) -> State:
        state_out = super().run(**kwargs)

        antennae_rpt_path = os.path.join(self.step_dir, "antennae.rpt")
        antennae_rpt = open(antennae_rpt_path).read()
        nets = get_antenna_nets(antennae_rpt)

        antennae_report_post_fix_path = os.path.join(
            self.step_dir, "antennae_post_fix.rpt"
        )
        if os.path.exists(antennae_report_post_fix_path):
            net_count_before = len(nets)

            antennae_rpt = open(antennae_rpt_path).read()
            nets = get_antenna_nets(antennae_rpt)
            net_count_after = len(nets)

            if net_count_before == net_count_after:
                log("Antenna count unchanged after OpenROAD antenna fixer.")
            elif net_count_after > net_count_before:
                warn(
                    "Inexplicably, the OpenROAD antenna fixer has generated more antennae. The flow may continue, but you may want to report a bug."
                )
            else:
                log(
                    f"Antenna count reduced using OpenROAD antenna fixer: {net_count_before} -> {net_count_after}"
                )

        state_out.metrics["antenna_nets"] = nets

        return state_out


@Step.factory.register("OpenROAD.DetailedRouting")
class DetailedRouting(OpenROADStep):
    name = "Detailed Routing"
    flow_control_variable = "RUN_DRT"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "drt.tcl")

    def run(self, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        if self.config.get("ROUTING_CORES") is None:
            env["ROUTING_CORES"] = str(os.cpu_count())
        return super().run(env=env, **kwargs)


@Step.factory.register("OpenROAD.LayoutSTA")
class LayoutSTA(OpenROADStep):
    name = "Layout STA"
    long_name = "Layout Static Timing Analysis"

    outputs = []

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "sta.tcl")

    def run(self, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        env["RUN_STANDALONE"] = "1"
        return super().run(env=env, **kwargs)


@Step.factory.register("OpenROAD.FillInsertion")
class FillInsertion(OpenROADStep):
    name = "Fill Insertion"
    flow_control_variable = "RUN_FILL_INSERTION"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "fill.tcl")


@Step.factory.register("OpenROAD.ParasiticsExtraction")
class ParasiticsExtraction(OpenROADStep):
    name = "Parasitics Extraction"

    # default inputs
    outputs = [DesignFormat.SPEF]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "rcx.tcl")

    def run(self, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        env["RCX_RULESET"] = f"{self.config['RCX_RULES']}"
        return super().run(env=env, **kwargs)


@Step.factory.register("OpenROAD.ParasiticsSTA")
class ParasiticsSTA(OpenROADStep):
    name = "Parasitics STA"
    long_name = "Parasitics-based Static Timing Analysis"

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


@Step.factory.register("OpenROAD.CheckAntennae")
class CheckAntennae(OpenROADStep):
    name = "Check Antennae"

    # default inputs
    outputs = []

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "check_antennae.tcl")

    def run(self, **kwargs) -> State:
        state_out = super().run(**kwargs)

        antennae_rpt = open(os.path.join(self.step_dir, "antennae.rpt")).read()

        state_out.metrics["antenna_nets"] = get_antenna_nets(antennae_rpt)

        return state_out


@Step.factory.register("OpenROAD.FixAntennae")
class FixAntennae(OpenROADStep):
    name = "Fix Antennae"

    # default inputs
    outputs = []

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "fix_antennae.tcl")

    def run(self, **kwargs) -> State:
        state_out = super().run(**kwargs)

        antennae_rpt = open(os.path.join(self.step_dir, "antennae.rpt")).read()

        before = state_out.metrics["antenna_nets"]

        after = get_antenna_nets(antennae_rpt)

        log(f"Reduced antenna violations from {len(before)} -> {len(after)}.")

        return state_out


@Step.factory.register("OpenROAD.IRDropReport")
class IRDropReport(OpenROADStep):
    name = "IR Drop Report"
    long_name = "Generate IR Drop Report"

    inputs = [DesignFormat.ODB, DesignFormat.SPEF]
    outputs = []

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
@Step.factory.register("OpenROAD.RepairDesign")
class RepairDesign(OpenROADStep):
    id = "repair-design"
    name = "Repair Design (Post-Global Placement)"
    flow_control_variable = "RUN_POST_GPL_REPAIR_DESIGN"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "repair_design.tcl")


@Step.factory.register("OpenROAD.ResizerTimingPostCTS")
class ResizerTimingPostCTS(OpenROADStep):
    id = "rsz-timing-postcts"
    name = "Resizer Timing Optimizations (Post-Clock Tree Synthesis)"
    flow_control_variable = "RUN_POST_CTS_RESIZER_TIMING"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "rsz_timing_postcts.tcl")


@Step.factory.register("OpenROAD.ResizerTimingPostGRT")
class ResizerTimingPostGRT(OpenROADStep):
    id = "rsz-timing-postgrt"
    name = "Resizer Timing Optimizations (Post-Global Routing)"
    flow_control_variable = "RUN_POST_GRT_RESIZER_TIMING"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "rsz_timing_postgrt.tcl")
