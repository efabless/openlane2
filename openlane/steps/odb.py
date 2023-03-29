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
import sys
import json
from decimal import Decimal
from abc import abstractmethod
from typing import List, Optional


from .step import Step
from ..state import State
from ..state import DesignFormat
from .common_variables import io_layer_variables

from ..config import Path, Variable, StringEnum
from ..common import get_openlane_root, get_script_dir
from ..logging import warn

inf_rx = re.compile(r"\b(-?)inf\b")


class OdbpyStep(Step):
    inputs = [DesignFormat.ODB]
    outputs = [DesignFormat.ODB, DesignFormat.DEF]

    def run(
        self,
        **kwargs,
    ) -> State:
        """
        TODO
        """

        state_out = super().run(**kwargs)
        kwargs, env = self.extract_env(kwargs)

        out_paths = {}

        command = self.get_command()
        for output in [DesignFormat.ODB, DesignFormat.DEF]:
            id, ext, _ = output.value
            filename = f"{self.config['DESIGN_NAME']}.{ext}"
            file_path = os.path.join(self.step_dir, filename)
            command.append(f"--output-{id}")
            command.append(file_path)
            out_paths[output] = Path(file_path)

        command += [
            str(state_out[DesignFormat.ODB]),
        ]

        env["OPENLANE_ROOT"] = get_openlane_root()
        env["ODB_PYTHONPATH"] = ":".join(sys.path)

        self.run_subprocess(
            command,
            env=env,
            **kwargs,
        )

        metrics_path = os.path.join(self.step_dir, "or_metrics_out.json")
        if os.path.exists(metrics_path):
            metrics_str = open(metrics_path).read()
            metrics_str = inf_rx.sub(lambda m: f"{m[1] or ''}\"Infinity\"", metrics_str)
            new_metrics = json.loads(metrics_str)
            state_out.metrics.update(new_metrics)

        for output in [DesignFormat.ODB, DesignFormat.DEF]:
            state_out[output] = out_paths[output]

        return state_out

    def get_command(self) -> List[str]:
        metrics_path = os.path.join(self.step_dir, "or_metrics_out.json")
        lefs = ["--input-lef", self.config["TECH_LEF"]]
        for lef in self.config["CELL_LEFS"]:
            lefs.append("--input-lef")
            lefs.append(lef)
        if extra_lefs := self.config["EXTRA_LEFS"]:
            for lef in extra_lefs:
                lefs.append("--input-lef")
                lefs.append(lef)
        return (
            [
                "openroad",
                "-exit",
                "-metrics",
                metrics_path,
                "-python",
                self.get_script_path(),
            ]
            + self.get_subcommand()
            + lefs
        )

    @abstractmethod
    def get_script_path(self):
        pass

    def get_subcommand(self) -> List[str]:
        return []


@Step.factory.register()
class ApplyDEFTemplate(OdbpyStep):
    id = "Odb.ApplyDEFTemplate"
    name = "Apply DEF Template"

    flow_control_variable = "FP_DEF_TEMPLATE"
    flow_control_msg = "No DEF template provided, skipping…"

    config_vars = [
        Variable(
            "FP_DEF_TEMPLATE",
            Optional[Path],
            "Points to the DEF file to be used as a template when running `apply_def_template`. This will be used to exctract pin names, locations, shapes -excluding power and ground pins- as well as the die area and replicate all this information in the `CURRENT_DEF`.",
        ),
    ]

    def get_script_path(self):
        return os.path.join(
            get_script_dir(),
            "odbpy",
            "apply_def_template.py",
        )

    def get_command(self) -> List[str]:
        return super().get_command() + [
            "--def-template",
            self.config["FP_DEF_TEMPLATE"],
        ]


@Step.factory.register()
class ManualMacroPlacement(OdbpyStep):
    id = "Odb.ManualMacro"
    name = "Manual Macro Placement"

    flow_control_variable = "MACRO_PLACEMENT_CFG"
    flow_control_msg = "No macros configured, skipping…"

    config_vars = [
        Variable(
            "MACRO_PLACEMENT_CFG",
            Optional[Path],
            "Specifies the path a file specifying how OpenLane should place certain macros.",
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "manual_macro_place.py")

    def get_command(self) -> List[str]:
        return super().get_command() + [
            "--config",
            self.config["MACRO_PLACEMENT_CFG"],
            "--fixed",
        ]


@Step.factory.register()
class ReportWireLength(OdbpyStep):
    id = "Odb.ReportWireLength"
    name = "Report Wire Length"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "wire_lengths.py")

    def get_command(self) -> List[str]:
        return super().get_command() + [
            "--human-readable",
            "--report-out",
            os.path.join(self.step_dir, "wire_lengths.csv"),
        ]


@Step.factory.register()
class CustomIOPlacement(OdbpyStep):
    id = "Odb.CustomIOPlacement"
    name = "Custom I/O Placement"
    long_name = "Custom I/O Pin Placement Script"

    flow_control_variable = "FP_PIN_ORDER_CFG"
    flow_control_msg = "No custom floorplan file configured, skipping…"

    config_vars = io_layer_variables + [
        Variable(
            "FP_PIN_ORDER_CFG",
            Optional[Path],
            "Points to the pin order configuration file to set the pins in specific directions (S, W, E, N). If not set, then the IO pins will be placed using OpenROAD's basic pin placer.",
        ),
        Variable(
            "QUIT_ON_UNMATCHED_IO",
            bool,
            "Exit on unmatched pins in a provided `FP_PIN_ORDER_CFG` file.",
            default=True,
            deprecated_names=["FP_IO_UNMATCHED_ERROR"],
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "io_place.py")

    def get_command(self) -> List[str]:
        length = max(
            self.config["FP_IO_VLENGTH"],
            self.config["FP_IO_HLENGTH"],
        )

        return super().get_command() + [
            "--config",
            self.config["FP_PIN_ORDER_CFG"],
            "--hor-layer",
            self.config["FP_IO_HLAYER"],
            "--ver-layer",
            self.config["FP_IO_VLAYER"],
            "--hor-width-mult",
            str(self.config["FP_IO_VTHICKNESS_MULT"]),
            "--ver-width-mult",
            str(self.config["FP_IO_HTHICKNESS_MULT"]),
            "--hor-extension",
            str(self.config["FP_IO_HEXTEND"]),
            "--ver-extension",
            str(self.config["FP_IO_VEXTEND"]),
            "--length",
            str(length),
            (
                "--unmatched-error"
                if self.config["QUIT_ON_UNMATCHED_IO"]
                else "--ignore-unmatched"
            ),
        ]


@Step.factory.register()
class DiodesOnPorts(OdbpyStep):
    id = "Odb.DiodesOnPorts"
    name = "Diodes on Ports"
    long_name = "Diode on Port Insertion Script"

    config_vars = [
        Variable(
            "DIODE_ON_PORTS",
            StringEnum("DIODE_ON_PORTS", ["none", "in", "out", "both"]),
            "Always insert diodes on ports with the specified polarities.",
            default="none",
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "diodes.py")

    def get_subcommand(self) -> List[str]:
        return ["place"]

    def get_command(self) -> List[str]:
        cell, pin = self.config["DIODE_CELL"].split("/")

        return super().get_command() + [
            "--threshold",
            "Infinity",
            "--diode-cell",
            cell,
            "--diode-pin",
            pin,
            "--port-protect",
            self.config["DIODE_ON_PORTS"].value,
        ]

    def run(self, **kwargs) -> State:
        if self.config["DIODE_ON_PORTS"].value == "none":
            warn("'DIODE_ON_PORTS' is set to 'none': skipping…")
            return Step.run(self, **kwargs)

        if self.config["GPL_CELL_PADDING"] == 0:
            warn(
                "'GPL_CELL_PADDING' is set to 0. This step may cause overlap failures."
            )

        return super().run(**kwargs)


@Step.factory.register()
class HeuristicDiodeInsertion(OdbpyStep):
    id = "Odb.HeuristicDiodeInsertion"
    name = "Heuristic Diode Insertion"
    long_name = "Heuristic Diode Insertion Script"

    flow_control_variable = "RUN_HEURISTIC_DIODE_INSERTION"
    config_vars = [
        Variable(
            "RUN_HEURISTIC_DIODE_INSERTION",
            bool,
            "Enables/disables this step.",
            default=False,  # For compatibility with OL1. Yep.
        ),
        Variable(
            "HEURISTIC_ANTENNA_THRESHOLD",
            Optional[Decimal],
            "A manhattan distance above which a diode is recommended to be inserted by a heuristic inserter. If not specified, the heuristic inserter will typically use a default value.",
            units="µm",
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "diodes.py")

    def get_subcommand(self) -> List[str]:
        return ["place"]

    def get_command(self) -> List[str]:
        cell, pin = self.config["DIODE_CELL"].split("/")

        threshold_opts = []
        if threshold := self.config["HEURISTIC_ANTENNA_THRESHOLD"]:
            threshold_opts = ["--threshold", threshold]

        return (
            super().get_command()
            + [
                "--diode-cell",
                cell,
                "--diode-pin",
                pin,
            ]
            + threshold_opts
        )

    def run(self, **kwargs) -> State:
        if self.config["GPL_CELL_PADDING"] == 0:
            warn(
                "'GPL_CELL_PADDING' is set to 0. This step may cause overlap failures."
            )

        return super().run(**kwargs)
