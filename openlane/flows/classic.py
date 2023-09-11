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
from typing import List, Type

from .flow import Flow
from .sequential import SequentialFlow
from ..config import Variable
from ..steps import (
    Step,
    Yosys,
    OpenROAD,
    Magic,
    KLayout,
    Odb,
    Netgen,
    Checker,
    Verilator,
)


@Flow.factory.register()
class Classic(SequentialFlow):
    """
    A flow of type :class:`openlane.flows.SequentialFlow` that is the most
    similar to the original OpenLane 1.0 flow, running the Verilog RTL through
    Yosys, OpenROAD, KLayout and Magic to produce a valid GDSII for simpler designs.

    This is the default when using OpenLane via the command-line.
    """

    Steps: List[Type[Step]] = [
        Verilator.Lint,
        Checker.LintTimingConstructs,
        Checker.LintErrors,
        Checker.LintWarnings,
        Yosys.JsonHeader,
        Yosys.Synthesis,
        Checker.YosysUnmappedCells,
        Checker.YosysSynthChecks,
        OpenROAD.CheckSDCFiles,
        OpenROAD.STAPrePNR,
        OpenROAD.Floorplan,
        Odb.SetPowerConnections,
        Odb.ManualMacroPlacement,
        OpenROAD.TapEndcapInsertion,
        OpenROAD.IOPlacement,
        Odb.CustomIOPlacement,
        Odb.ApplyDEFTemplate,
        OpenROAD.GeneratePDN,
        OpenROAD.GlobalPlacement,
        OpenROAD.STAMidPNR,
        OpenROAD.RepairDesign,
        Odb.DiodesOnPorts,
        Odb.HeuristicDiodeInsertion,
        OpenROAD.DetailedPlacement,
        OpenROAD.CTS,
        OpenROAD.STAMidPNR,
        OpenROAD.ResizerTimingPostCTS,
        OpenROAD.STAMidPNR,
        OpenROAD.GlobalRouting,
        OpenROAD.ResizerTimingPostGRT,
        OpenROAD.STAMidPNR,
        OpenROAD.DetailedRouting,
        Checker.TrDRC,
        Odb.ReportDisconnectedPins,
        Checker.DisconnectedPins,
        Odb.ReportWireLength,
        Checker.WireLength,
        OpenROAD.FillInsertion,
        OpenROAD.RCX,
        OpenROAD.STAPostPNR,
        OpenROAD.IRDropReport,
        Magic.StreamOut,
        KLayout.StreamOut,
        Magic.WriteLEF,
        KLayout.XOR,
        Checker.XOR,
        Magic.DRC,
        Checker.MagicDRC,
        Magic.SpiceExtraction,
        Checker.IllegalOverlap,
        Netgen.LVS,
        Checker.LVS,
    ]

    gating_config_vars = {
        "Verilator.Lint": Variable(
            "RUN_LINTER",
            bool,
            "Enables the Verilator.Lint step.",
            default=True,
            deprecated_names=["RUN_VERILATOR"],
        ),
        "Checker.LintErrors": Variable(
            "QUIT_ON_LINTER_ERRORS",
            bool,
            "Quit immediately on any linter errors.",
            default=True,
            deprecated_names=["QUIT_ON_VERILATOR_ERRORS"],
        ),
        "Checker.LintWarnings": Variable(
            "QUIT_ON_LINTER_WARNINGS",
            bool,
            "Quit immediately on any linter warnings.",
            default=False,
            deprecated_names=["QUIT_ON_VERILATOR_WARNINGS"],
        ),
        "Checker.LintTimingConstructs": Variable(
            "QUIT_ON_LINTER_TIMING_CONSTRUCTS",
            bool,
            "Quit immediately on any discovered timing constructs during linting.",
            default=True,
            deprecated_names=["QUIT_ON_LINTER_TIMING_CONSTRUCTS"],
        ),
        "OpenROAD.RepairDesign": Variable(
            "RUN_REPAIR_DESIGN",
            bool,
            "Enables resizer design repair using the OpenROAD.RepairDesign step.",
            default=True,
            deprecated_names=["PL_RESIZER_DESIGN_OPTIMIZATIONS"],
        ),
        "OpenROAD.CTS": Variable(
            "RUN_CTS",
            bool,
            "Enables clock tree synthesis using the OpenROAD.CTS step.",
            default=True,
            deprecated_names=["CLOCK_TREE_SYNTH"],
        ),
        "OpenROAD.ResizerTimingPostCTS": Variable(
            "RUN_POST_CTS_RESIZER_TIMING",
            bool,
            "Enables resizer timing optimizations after clock tree synthesis using the OpenROAD.ResizerTimingPostCTS step.",
            default=True,
            deprecated_names=["PL_RESIZER_TIMING_OPTIMIZATIONS"],
        ),
        "OpenROAD.RCX": Variable(
            "RUN_SPEF_EXTRACTION",
            bool,
            "Enables parasitics extraction using the OpenROAD.RCX step.",
            default=True,
        ),
        "OpenROAD.TapEndcapInsertion": Variable(
            "RUN_TAP_ENDCAP_INSERTION",
            bool,
            "Enables the OpenROAD.TapEndcapInsertion step.",
            default=True,
            deprecated_names=["TAP_DECAP_INSERTION", "RUN_TAP_DECAP_INSERTION"],
        ),
        "OpenROAD.ResizerTimingPostGRT": Variable(
            "RUN_POST_GRT_RESIZER_TIMING",
            bool,
            "Enables resizer timing optimizations after global routing using the OpenROAD.ResizerTimingPostGRT step.",
            default=True,
            deprecated_names=["GLB_RESIZER_TIMING_OPTIMIZATIONS"],
        ),
        "OpenROAD.DetailedRouting": Variable(
            "RUN_DRT",
            bool,
            "Enables the OpenROAD.DetailedRouting step.",
            default=True,
        ),
        "OpenROAD.FillInsertion": Variable(
            "RUN_FILL_INSERTION",
            bool,
            "Enables the OpenROAD.FillInsertion step.",
            default=True,
        ),
        "OpenROAD.STAPostPNR": Variable(
            "RUN_MCSTA",
            bool,
            "Enables multi-corner static timing analysis using the OpenROAD.STAPostPNR step.",
            default=True,
            deprecated_names=["RUN_SPEF_STA"],
        ),
        "OpenROAD.IRDropReport": Variable(
            "RUN_IRDROP_REPORT",
            bool,
            "Enables generation of an IR Drop report using the OpenROAD.IRDropReport step.",
            default=True,
        ),
        "Odb.HeuristicDiodeInsertion": Variable(
            "RUN_HEURISTIC_DIODE_INSERTION",
            bool,
            "Enables the Odb.HeuristicDiodeInsertion step.",
            default=False,  # For compatibility with OL1
        ),
        "Netgen.LVS": Variable(
            "RUN_LVS",
            bool,
            "Enables the Netgen.LVS step.",
            default=True,
        ),
        "Magic.DRC": Variable(
            "RUN_MAGIC_DRC",
            bool,
            "Enables the Magic.DRC step.",
            default=True,
        ),
        "Magic.StreamOut": Variable(
            "RUN_MAGIC_STREAMOUT",
            bool,
            "Enables the Magic.StreamOut step to generate GDSII.",
            default=True,
            deprecated_names=["RUN_MAGIC"],
        ),
        "Magic.WriteLEF": Variable(
            "RUN_MAGIC_WRITE_LEF",
            bool,
            "Enables the Magic.WriteLEF step.",
            default=True,
            deprecated_names=["MAGIC_GENERATE_LEF"],
        ),
        "KLayout.StreamOut": Variable(
            "RUN_KLAYOUT_STREAMOUT",
            bool,
            "Enables the KLayout.StreamOut step to generate GDSII.",
            default=True,
            deprecated_names=["RUN_KLAYOUT"],
        ),
        "KLayout.XOR": Variable(
            "RUN_KLAYOUT_XOR",
            bool,
            "Enables running the KLayout.XOR step on the two GDSII files generated by Magic and Klayout. Stream-outs for both KLayout and Magic should have already run, and the PDK must support both signoff tools.",
            default=True,
        ),
        "Checker.YosysUnmappedCells": Variable(
            "QUIT_ON_UNMAPPED_CELLS",
            bool,
            "Checks for unmapped cells after synthesis and quits immediately if so.",
            deprecated_names=["CHECK_UNMAPPED_CELLS"],
            default=True,
        ),
        "Checker.YosysChecks": Variable(
            "QUIT_ON_SYNTH_CHECKS",
            bool,
            "Quits the flow immediately if one or more synthesis check errors are flagged. This checks for combinational loops and/or wires with no drivers.",
            default=True,
        ),
        "Checker.TrDRC": Variable(
            "QUIT_ON_TR_DRC",
            bool,
            "Checks for DRC violations after routing and exits the flow if any was found.",
            default=True,
        ),
        "Checker.MagicDRC": Variable(
            "QUIT_ON_MAGIC_DRC",
            bool,
            "Checks for DRC violations after magic DRC is executed and exits the flow if any was found.",
            default=True,
        ),
        "Checker.DisconnectedPins": Variable(
            "QUIT_ON_DISCONNECTED_PINS",
            bool,
            "Checks for disconnected instance pins after detailed routing and quits immediately if so.",
            default=True,
        ),
        "Checker.WireLength": Variable(
            "QUIT_ON_LONG_WIRE",
            bool,
            "Checks if any wire length exceeds the threshold set in the PDK. If so, an error is raised at the end of the flow.",
            default=False,
        ),
        "Checker.XOR": Variable(
            "QUIT_ON_XOR_ERROR",
            bool,
            "Checks for geometric differences between the Magic and KLayout stream-outs. If any exist, raise an error at the end of the flow.",
            default=True,
        ),
        "Checker.IllegalOverlap": Variable(
            "QUIT_ON_ILLEGAL_OVERLAPS",
            bool,
            "Checks for illegal overlaps during Magic extraction. In some cases, these imply existing undetected shorts in the design. It raises an error at the end of the flow if so.",
            default=True,
        ),
        "Checker.LVS": Variable(
            "QUIT_ON_LVS_ERROR",
            bool,
            "Checks for LVS errors after Netgen is executed. If any exist, it raises an error at the end of the flow.",
            default=True,
        ),
        # "KLayout.DRC": Variable(
        #     "RUN_KLAYOUT_DRC",
        #     bool,
        #     "Enables running KLayout DRC on GDSII produced by magic.",
        #     default=False,
        # ),
    }
