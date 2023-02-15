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
from typing import List

from .step import Step
from .state import State
from .design_format import DesignFormat
from ..common import get_openlane_root, get_script_dir, log
from ..config import Path

inf_rx = re.compile(r"\b(-?)inf\b")


class OdbpyStep(Step):
    """
    TODO
    """

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

        log_filename = os.path.splitext(os.path.basename(self.get_script_path()))[0]
        log_path = os.path.join(self.step_dir, f"{log_filename}.log")

        self.run_subprocess(
            command,
            env=env,
            log_to=log_path,
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
        return [
            "openroad",
            "-exit",
            "-metrics",
            metrics_path,
            "-python",
            self.get_script_path(),
        ]

    @abstractmethod
    def get_script_path(self):
        pass


@Step.factory.register("Odb.ManualMacro")
class ManualMacroPlacement(OdbpyStep):
    name = "Manual Macro Placement"

    flow_control_variable = "MACRO_PLACEMENT_CFG"
    flow_control_msg = "No macros configured, skipping…"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "manual_macro_place.py")

    def get_command(self) -> List[str]:
        return super().get_command() + [
            "--config",
            self.config["MACRO_PLACEMENT_CFG"],
            "--fixed",
        ]


@Step.factory.register("Odb.ReportWireLength")
class ReportWireLength(OdbpyStep):
    name = "Report Wire Length"

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "wire_lengths.py")

    def get_command(self) -> List[str]:
        return super().get_command() + [
            "--human-readable",
            "--report-out",
            os.path.join(self.step_dir, "wire_lengths.csv"),
        ]


@Step.factory.register("Odb.CustomIOPlacement")
class CustomIOPlacement(OdbpyStep):
    id = "custom_io_placement"
    name = "Custom I/O Placement"
    long_name = "Custom I/O Pin Placement Script"

    flow_control_variable = "FP_PIN_ORDER_CFG"
    flow_control_msg = "No custom floorplan file configured, skipping…"

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
