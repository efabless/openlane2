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
import textwrap
from typing import Tuple

from .step import ViewsUpdate, MetricsUpdate, Step
from ..common import Path
from ..state import State, DesignFormat
from ..steps import Netgen, Magic, KLayout, OpenROAD
from ..logging import warn, options


@Step.factory.register()
class LoadBaseSDC(Step):
    """
    Loads an SDC file specified as a configuration variable into the state
    object unaltered.

    This Step exists for legacy compatibility and should not be used
    in new flows.
    """

    id = "Misc.LoadBaseSDC"
    name = "Load Base SDC"
    long_name = "Load Base Design Constraints File"

    inputs = []
    outputs = [DesignFormat.SDC]

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        path = self.config["FALLBACK_SDC_FILE"]

        target = os.path.join(self.step_dir, f"{self.config['DESIGN_NAME']}.sdc")

        # Otherwise, you'll end up with weird permissions and may have to chmod
        with open(target, "w", encoding="utf8") as out:
            for line in open(path, "r", encoding="utf8"):
                out.write(line)

        return {DesignFormat.SDC: Path(target)}, {}


@Step.factory.register()
class ReportManufacturability(Step):
    id = "Misc.ReportManufacturability"
    name = "Report Manufacturability"
    long_name = "Report Manufacturability (DRC, LVS, Antenna)"
    inputs = []
    outputs = []

    def __get_lvs_report(self, state_in):
        lvs_step = Netgen.LVS.id
        report = []
        report.append(
            textwrap.dedent(
                """
                ██╗    ██╗   ██╗███████╗
                ██║    ██║   ██║██╔════╝
                ██║    ██║   ██║███████╗
                ██║    ╚██╗ ██╔╝╚════██║
                ███████╗╚████╔╝ ███████║
                ╚══════╝ ╚═══╝  ╚══════╝
                """
            )
        )
        try:
            total = state_in.metrics["design__lvs_errors__count"]
            unmatched_pins = state_in.metrics["design__lvs_unmatched_pins__count"]
            unmatched_nets = state_in.metrics["design__lvs_unmatched_nets__count"]
            if total == 0:
                report.append("Passed ✅")
            else:
                report.append("Failed 𐄂")
                report.append(f"Total Errors: {total}")
                report.append(f"Unmatched Pins: {unmatched_pins}")
                report.append(f"Unmatched Nets: {unmatched_nets}")
                report.append(f"Check {lvs_step} report directory")
        except KeyError as key:
            warn(f"{key} not reported. Perhaps step: {lvs_step} didn't run.")
            report.append("N/A")

        return "\n".join(report)

    def __get_drc_report(self, state_in):
        klayout_step = KLayout.DRC.id
        magic_step = Magic.DRC.id
        klayout_failed = False
        magic_failed = False
        report = []

        report.append(
            textwrap.dedent(
                """
                ██████╗ ██████╗  ██████╗
                ██╔══██╗██╔══██╗██╔════╝
                ██║  ██║██████╔╝██║     
                ██║  ██║██╔══██╗██║     
                ██████╔╝██║  ██║╚██████╗
                ╚═════╝ ╚═╝  ╚═╝ ╚═════╝
                """
            )
        )

        klayout = state_in.metrics.get("klayout__drc_error__count", "N/A")
        if klayout == "N/A":
            warn(
                f"klayout__drc_error__count not reported. Perhaps step: {klayout_step} didn't run."
            )
        elif klayout > 0:
            klayout_failed = True

        magic = state_in.metrics.get("magic__drc_error__count", "N/A")
        if magic == "N/A":
            warn(
                f"magic__drc_error__count not reported. Perhaps step: {magic_step} didn't run."
            )
        elif magic > 0:
            magic_failed = True

        if magic == "N/A" and klayout == "N/A":
            report.append("N/A")
        elif magic_failed or klayout_failed:
            report.append("Failed 𐄂")
            report.append(f"KLayout DRC errors: {klayout}")
            report.append(f"Magic DRC errors: {magic}")
            report.append(f"Check {klayout_step} and {magic_step} report directories")
        else:
            report.append("Passed ✅")

        return "\n".join(report)

    def __get_antenna_report(self, state_in):
        antenna_step = OpenROAD.CheckAntennas.id
        report = []
        report.append(
            textwrap.dedent(
                """
             █████╗ ███╗   ██╗████████╗███████╗███╗   ██╗███╗   ██╗ █████╗ 
            ██╔══██╗████╗  ██║╚══██╔══╝██╔════╝████╗  ██║████╗  ██║██╔══██╗
            ███████║██╔██╗ ██║   ██║   █████╗  ██╔██╗ ██║██╔██╗ ██║███████║
            ██╔══██║██║╚██╗██║   ██║   ██╔══╝  ██║╚██╗██║██║╚██╗██║██╔══██║
            ██║  ██║██║ ╚████║   ██║   ███████╗██║ ╚████║██║ ╚████║██║  ██║
            ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚═╝  ╚═╝
            """
            )
        )

        try:
            nets = state_in.metrics["antenna__violating__nets"]
            pins = state_in.metrics["antenna__violating__pins"]
            if pins + nets == 0:
                report.append("Passed ✅")
            else:
                report.append("Failed 𐄂")
                report.append(f"Pin violations: {pins}")
                report.append(f"Net violations: {nets}")
                report.append(f"Check {antenna_step} report directory")
        except KeyError as key:
            warn(f"{key} not reported. Perhaps step: {antenna_step} didn't run.")
            report.append("N/A")

        return "\n".join(report)

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        report_file = os.path.join(self.step_dir, "manufacturability.rpt")
        lvs_report = self.__get_lvs_report(state_in)
        drc_report = self.__get_drc_report(state_in)
        antenna_report = self.__get_antenna_report(state_in)
        if not options.get_condensed_mode():
            print(antenna_report)
            print(lvs_report)
            print(drc_report)

        with open(report_file, "w") as f:
            print(antenna_report, file=f)
            print(lvs_report, file=f)
            print(drc_report, file=f)
        return {}, {}
