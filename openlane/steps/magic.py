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
from typing import List
from abc import abstractmethod

from .step import Step
from .tclstep import TclStep
from .state import DesignFormat, State
from ..common import get_script_dir
from ..utils import DRC as DRCObject


class MagicStep(TclStep):
    inputs = [DesignFormat.GDS]
    outputs = []

    @abstractmethod
    def get_script_path(self):
        pass

    def get_command(self) -> List[str]:
        return [
            "magic",
            "-dnull",
            "-noconsole",
            "-rcfile",
            str(self.config["MAGICRC"]),
        ]

    def run(self, **kwargs) -> State:
        # https://github.com/RTimothyEdwards/magic/issues/218
        kwargs["stdin"] = open(self.get_script_path(), encoding="utf8")
        return super().run(**kwargs)


@Step.factory.register("Magic.StreamOut")
class StreamOut(MagicStep):
    id = "magic-streamout"
    name = "GDS-II Stream Out (Magic)"
    flow_control_variable = "RUN_MAGIC_STREAMOUT"

    inputs = [DesignFormat.DEF]
    outputs = [DesignFormat.GDS, DesignFormat.MAG_GDS]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "magic", "def", "mag_gds.tcl")

    def run(self, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        assert isinstance(self.state_in, State)
        if diea_area := self.state_in.metrics.get("die__area"):
            env["DIE_AREA"] = diea_area

        state_out = super().run(env=env, **kwargs)
        if self.config["PRIMARY_SIGNOFF_TOOL"].value == "magic":
            state_out[DesignFormat.GDS] = state_out[DesignFormat.MAG_GDS]
        return state_out


@Step.factory.register("Magic.DRC")
class DRC(MagicStep):
    name = "DRC"
    long_name = "Design Rule Checks"

    flow_control_variable = "RUN_MAGIC_DRC"

    inputs = [DesignFormat.DEF, DesignFormat.GDS]
    outputs = []

    def get_script_path(self):
        return os.path.join(get_script_dir(), "magic", "drc.tcl")

    def run(self, **kwargs) -> State:
        state_out = super().run(**kwargs)

        reports_dir = os.path.join(self.step_dir, "reports")
        report_path = os.path.join(reports_dir, "drc.rpt")
        report_str = open(report_path, encoding="utf8").read()

        drc = DRCObject.from_magic(report_str)
        state_out.metrics["magic__drc_errors"] = len(drc.violations)

        with open(os.path.join(reports_dir, "drc.klayout.xml"), "w") as f:
            f.write(drc.to_klayout_xml())

        return state_out


@Step.factory.register("Magic.SpiceExtraction")
class SpiceExtraction(MagicStep):
    name = "SPICE Extraction"
    long_name = "SPICE Model Extraction"

    inputs = [DesignFormat.GDS, DesignFormat.DEF]
    outputs = [DesignFormat.SPICE]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "magic", "extract_spice.tcl")

    def run(self, **kwargs) -> State:
        state_out = super().run(**kwargs)

        feedback_path = os.path.join(self.step_dir, "feedback.txt")
        feedback_string = open(feedback_path, encoding="utf8").read()
        state_out.metrics["magic__illegal__overlaps"] = "Illegal overlap".count(
            feedback_string
        )
        return state_out
