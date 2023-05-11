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
import glob
import json
from typing import List, Dict
from abc import abstractmethod

from .step import Step
from .tclstep import TclStep

from ..logging import info
from ..config import Variable, Keys
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
    metrics["design__lvs_net_differences__count"] = net_differences
    metrics["design__lvs_property_fails__count"] = property_fails
    metrics["design__lvs_errors__count"] = total_errors
    metrics["design__lvs_unmatched_devices__count"] = device_fails
    metrics["design__lvs_unmatched_nets__count"] = net_fails
    metrics["design__lvs_unmatched_pins__count"] = pin_fails

    return metrics


class NetgenStep(TclStep):
    inputs = []
    outputs = []

    @abstractmethod
    def get_script_path(self):
        pass

    def get_command(self) -> List[str]:
        return ["netgen", "-batch", "source"]


@Step.factory.register()
class LVS(NetgenStep):
    """
    Performs `Layout vs. Schematic <https://en.wikipedia.org/wiki/Layout_Versus_Schematic>`_ checks on the extracted SPICE netlist versus.
    a verilog netlist with power connections.

    This verifies the following:
    * There are no unexpected shorts in the final layout.
    * There are no unexpected opens in the final layout.
    * All signals are connected correctly.
    """

    id = "Netgen.LVS"
    inputs = [DesignFormat.SPICE, DesignFormat.POWERED_NETLIST]
    flow_control_variable = "RUN_LVS"

    config_vars = [
        Variable(
            "RUN_LVS",
            bool,
            "Enables running LVS.",
            default=True,
        ),
    ]

    def get_command(self) -> List[str]:
        return super().get_command() + [self.get_script_path()]

    def get_script_path(self):
        return os.path.join(self.step_dir, "lvs_script.lvs")

    def run(self, state_in: State, **kwargs) -> State:
        if self.config["NETGEN_SETUP"] is None:
            info(f"Skipping {self.name}: Netgen is not supported for this PDK.")
            return Step.run(self, state_in, **kwargs)

        spice_glob = os.path.join(
            self.config[Keys.pdk_root],
            self.config[Keys.pdk],
            "libs.ref",
            self.config[Keys.scl],
            "spice",
            "*.spice",
        )
        spice_files: List[str] = glob.glob(spice_glob)

        if pdk_spice_files := self.config.get("SPICE_MODELS"):
            spice_files = pdk_spice_files.copy()

        if extra_spice_files := self.config.get("EXTRA_SPICE_MODELS"):
            spice_files += extra_spice_files

        design_name = self.config["DESIGN_NAME"]

        with open(self.get_script_path(), "w") as f:
            for lib in spice_files:
                print(
                    f"puts \"Reading SPICE netlist file '{lib}'...\"",
                    file=f,
                )
                print(
                    f"readnet spice {lib} 1",
                    file=f,
                )

            print(
                f"lvs {{ {state_in[DesignFormat.SPICE]} {design_name} }} {{ {state_in[DesignFormat.POWERED_NETLIST]} {design_name} }} {self.config['NETGEN_SETUP']} {os.path.abspath(self.step_dir)}/lvs.rpt -json",
                file=f,
            )

        state_out = super().run(state_in, **kwargs)
        stats_file = os.path.join(self.step_dir, "lvs.json")
        stats_string = open(stats_file).read()
        lvs_metrics = get_metrics(json.loads(stats_string))
        state_out.metrics.update(lvs_metrics)

        return state_out
