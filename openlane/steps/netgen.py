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
import textwrap
from decimal import Decimal
from abc import abstractmethod
from typing import List, Dict, Tuple

from .step import ViewsUpdate, MetricsUpdate, Step
from .tclstep import TclStep

from ..common import Path, mkdirp
from ..logging import warn
from ..config import Variable
from ..state import DesignFormat, State


def get_metrics(stats: Dict) -> Dict:
    metrics: Dict = {}
    if not stats:
        return metrics

    pin_fails = 0
    property_fails = 0
    net_differences = 0
    device_differences = 0
    top_cell = stats[-1]

    def filter_list_dict(list, element):
        return [i[element] for i in list if i.get(element)]

    def flatten(list):
        return [item for sublist in list for item in sublist]

    property_fails += len(flatten(filter_list_dict(stats, "properties")))
    net_fails = len(top_cell.get("badnets", []))
    device_fails = len(top_cell.get("badelements", []))

    nets = top_cell.get("nets", [0, 0])
    net_differences = abs(nets[0] - nets[1])

    if "devices" in top_cell:
        devices = top_cell["devices"]
        devlist = [val for pair in zip(devices[0], devices[1]) for val in pair]
        devpair = list(devlist[p : p + 2] for p in range(0, len(devlist), 2))
        for dev in devpair:
            c1dev = dev[0]
            c2dev = dev[1]
            device_differences += abs(c1dev[1] - c2dev[1])

    if "pins" in top_cell:
        pins = top_cell["pins"]
        pinlist = [val for pair in zip(pins[0], pins[1]) for val in pair]
        pinpair = list(pinlist[p : p + 2] for p in range(0, len(pinlist), 2))
        for pin in pinpair:
            # Avoid flagging global vs. local names, e.g., "gnd" vs. "gnd!,"
            # and ignore case when comparing pins.
            pin0 = re.sub("!$", "", pin[0].lower())
            pin1 = re.sub("!$", "", pin[1].lower())
            if pin0 != pin1:
                # The text "(no pin)" indicates a missing pin that can be
                # ignored because the pin in the other netlist is a no-connect
                if pin0 != "(no pin)" and pin1 != "(no pin)":
                    pin_fails += 1

    total_errors = (
        device_differences
        + net_differences
        + property_fails
        + device_fails
        + net_fails
        + pin_fails
    )
    metrics = {}
    metrics["design__lvs_device_difference__count"] = device_differences
    metrics["design__lvs_net_difference__count"] = net_differences
    metrics["design__lvs_property_fail__count"] = property_fails
    metrics["design__lvs_error__count"] = total_errors
    metrics["design__lvs_unmatched_device__count"] = device_fails
    metrics["design__lvs_unmatched_net__count"] = net_fails
    metrics["design__lvs_unmatched_pin__count"] = pin_fails

    return metrics


class NetgenStep(TclStep):
    inputs = []
    outputs = []

    config_vars = [
        Variable(
            "MAGIC_EXT_USE_GDS",
            bool,
            "A flag to choose whether to use GDS for spice extraction or not. If not, then the extraction will be done using the DEF/LEF, which is faster.",
            default=False,
        ),
        Variable(
            "NETGEN_SETUP",
            Path,
            "A path to the setup file for Netgen used to configure LVS. If set to None, this PDK will not support Netgen-based steps.",
            deprecated_names=["NETGEN_SETUP_FILE"],
            pdk=True,
        ),
        Variable(
            "NETGEN_INCLUDE_MARCOS_NETLIST",
            bool,
            "A flag that enables including the gate-level netlist of the design while running Netgen",
            default=True,
        ),
    ]

    @abstractmethod
    def get_script_path(self) -> str:
        pass

    def get_command(self) -> List[str]:
        return ["netgen", "-batch", "source"]


@Step.factory.register()
class LVS(NetgenStep):
    """
    Performs `Layout vs. Schematic <https://en.wikipedia.org/wiki/Layout_Versus_Schematic>`_ checks on the extracted SPICE netlist versus.
    a Verilog netlist with power connections.

    This verifies the following:
    * There are no unexpected shorts in the final layout.
    * There are no unexpected opens in the final layout.
    * All signals are connected correctly.
    """

    id = "Netgen.LVS"
    name = "Netgen LVS"
    inputs = [DesignFormat.SPICE, DesignFormat.POWERED_NETLIST]

    def get_command(self) -> List[str]:
        return super().get_command() + [self.get_script_path()]

    def get_script_path(self):
        return os.path.join(self.step_dir, "lvs_script.lvs")

        #    def get_script_path(self):
        #        return "/home/karim/work/caravel_user_project/lvs/user_project_wrapper/lvs_results/2024-02-01-11-49-05/tmp/lvs.script"

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        spice_files = []
        if self.config["CELL_SPICE_MODELS"] is None:
            warn(
                "This PDK does not appear to define any SPICE models. LVS will still run, but all cells will be black-boxed and the result may be inaccurate."
            )
        else:
            spice_files = self.config["CELL_SPICE_MODELS"].copy()

        if pdk_spice_files := self.config.get("SPICE_MODELS"):
            spice_files = pdk_spice_files.copy()

        if extra_spice_files := self.config.get("EXTRA_SPICE_MODELS"):
            spice_files += extra_spice_files

        design_name = self.config["DESIGN_NAME"]
        reports_dir = os.path.join(self.step_dir, "reports")
        stats_file = os.path.join(reports_dir, "lvs.rpt")
        stats_file_json = os.path.join(reports_dir, "lvs.json")
        netgen_setup = os.path.join(self.step_dir, "setup.tcl")
        mkdirp(reports_dir)

        netgen_extra = textwrap.dedent(
            r"""
#---------------------------------------------------------------
# Equate sram layout cells with corresponding source
foreach cell $cells1 {
    if {[regexp {([A-Z][A-Z0-9]_)*sky130_sram_([^_]+)_([^_]+)_([^_]+)_([^_]+)_(.+)} $cell match prefix memory_size memory_type matrix io cellname]} {
        if {([lsearch $cells2 $cell] < 0) && \
            ([lsearch $cells2 $cellname] >= 0) && \
            ([lsearch $cells1 $cellname] < 0)} {
            # netlist with the N names should always be the second netlist
            equate classes "-circuit2 $cellname" "-circuit1 $cell"
            puts stdout "Equating $cell in circuit 1 and $cellname in circuit 2"
            #equate pins "-circuit1 $cell" "-circuit2 $cellname"
        }
    }
}

# Equate prefixed layout cells with corresponding source
foreach cell $cells1 {
    set layout $cell
    while {[regexp {([A-Z][A-Z0-9]_)(.*)} $layout match prefix cellname]} {
        if {([lsearch $cells2 $cell] < 0) && \
            ([lsearch $cells2 $cellname] >= 0)} {
            # netlist with the N names should always be the second netlist
            equate classes "-circuit2 $cellname" "-circuit1 $cell"
            puts stdout "Equating $cell in circuit 1 and $cellname in circuit 2"
        }
        set layout $cellname
    }
}

# Equate suffixed layout cells with corresponding source
foreach cell $cells1 {
    if {[regexp {(.*)(\$[0-9])} $cell match cellname suffix]} {
        if {([lsearch $cells2 $cell] < 0) && \
            ([lsearch $cells2 $cellname] >= 0)} {
            # netlist with the N names should always be the second netlist
            equate classes "-circuit2 $cellname" "-circuit1 $cell"
            puts stdout "Equating $cell in circuit 1 and $cellname in circuit 2"
        }
    }
}
        """
        )
        with open(netgen_setup, "w") as f:
            f.write(open(self.config["NETGEN_SETUP"]).read())
            f.write(netgen_extra)
        spice_files_commands = []
        for lib in spice_files:
            spice_files_commands.append(
                f"puts \"Reading SPICE netlist file '{lib}'...\""
            )
            spice_files_commands.append(f"readnet spice {lib} $circuit2")

        macros_commands = []
        macros = self.config.get("MACROS")
        if self.config["NETGEN_INCLUDE_MARCOS_NETLIST"] and macros:
            for macro_name in macros:
                nls = macros[macro_name].nl
                for nl in nls:
                    macros_commands.append(
                        f"puts \"Reading Verilog netlist file '{str(nl)}'...\""
                    )
                    macros_commands.append(f"readnet verilog {str(nl)} $circuit2")

        netgen_commands = (
            textwrap.dedent(
                f"""
                    set circuit1 [readnet spice {state_in[DesignFormat.SPICE]}]
                    set circuit2 [readnet verilog {state_in[DesignFormat.POWERED_NETLIST]}]"""
            )
        ).split("\n")
        netgen_commands += spice_files_commands
        netgen_commands += macros_commands
        netgen_commands += f'lvs "$circuit1 {design_name}" "$circuit2 {design_name}" {netgen_setup} {stats_file} -blackbox -json'.split(
            "\n"
        )
        with open(self.get_script_path(), "w") as f:
            print(
                "\n".join(netgen_commands),
                file=f,
            )
        views_updates, metrics_updates = super().run(state_in, **kwargs)
        stats_string = open(stats_file_json).read()
        lvs_metrics = get_metrics(json.loads(stats_string, parse_float=Decimal))
        metrics_updates.update(lvs_metrics)

        return (views_updates, metrics_updates)
