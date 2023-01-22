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
from typing import List, Dict, Tuple

from .step import TclStep, get_script_dir
from .state import State, DesignFormat, Output

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
        Output(DesignFormat.ODB),
        Output(DesignFormat.DEF),
        Output(DesignFormat.SDF),
        Output(DesignFormat.NETLIST),
        Output(DesignFormat.POWERED_NETLIST),
    ]

    def get_script_path(self):
        raise Exception("Subclass the OpenROAD Step class before using it.")

    def run(
        self,
        **kwargs,
    ) -> State:
        kwargs, env = self.extract_env(kwargs)

        lib_pnr = self.toolbox.libtools.remove_cells(
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


class NetlistSTA(OpenROADStep):
    name = "Netlist STA"
    long_name = "Netlist Static Timing Analysis"
    inputs = [DesignFormat.NETLIST]
    outputs = [Output(DesignFormat.LIB)]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "sta.tcl")

    def run(self, **kwargs) -> State:
        env = os.environ.copy()
        env["RUN_STANDALONE"] = "1"
        env["STA_PRE_CTS"] = "1"
        env["STA_REPORT_POWER"] = "1"
        return super().run(env=env, **kwargs)


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

        env = os.environ.copy()
        env["TRACKS_INFO_FILE_PROCESSED"] = new_tracks_info
        return super().run(env=env, **kwargs)


class IOPlacement(OpenROADStep):
    name = "I/O Placement"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "ioplacer.tcl")


class TapDecapInsertion(OpenROADStep):
    name = "Tap/Decap Insertion"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "tapcell.tcl")


class GeneratePDN(OpenROADStep):
    name = "Generate PDN"
    long_name = "Power Distribution Network Generation"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "pdn.tcl")


class GlobalPlacement(OpenROADStep):
    name = "Global Placement"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "gpl.tcl")

    def run(self, **kwargs) -> State:
        env = os.environ.copy()
        env["PL_TARGET_DENSITY"] = f"{self.config['FP_CORE_UTIL'] + 5}"
        return super().run(env=env, **kwargs)


class DetailedPlacement(OpenROADStep):
    name = "Detailed Placement"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "dpl.tcl")


class CTS(OpenROADStep):
    long_name = "Clock Tree Synthesis"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "cts.tcl")


class GlobalRouting(OpenROADStep):
    name = "Global Routing"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "grt.tcl")


class DetailedRouting(OpenROADStep):
    name = "Detailed Routing"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "drt.tcl")


class FillInsertion(OpenROADStep):
    name = "Fill Insertion"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "fill.tcl")


class ParasiticsExtraction(OpenROADStep):
    name = "Parasitics Extraction"

    # default inputs
    outputs = [Output(DesignFormat.SPEF)]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "rcx.tcl")

    def run(self, **kwargs) -> State:
        env = os.environ.copy()
        env["RCX_RULESET"] = f"{self.config['RCX_RULES']}"
        return super().run(env=env, **kwargs)


class ParasiticsSTA(OpenROADStep):
    name = "Parasitics STA"

    inputs = OpenROADStep.inputs + [DesignFormat.SPEF]
    outputs = [Output(DesignFormat.LIB)]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "openroad", "sta.tcl")

    def run(self, **kwargs) -> State:
        env = os.environ.copy()
        env["RUN_STANDALONE"] = "1"
        return super().run(env=env, **kwargs)
