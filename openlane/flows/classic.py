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
        OpenROAD.GlobalPlacementSkipIO,
        OpenROAD.IOPlacement,
        Odb.ApplyDEFTemplate,
        Odb.CustomIOPlacement,
        OpenROAD.GlobalPlacement,
        OpenROAD.GeneratePDN,
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
        Yosys.EQY,
    ]

    config_vars = [
        Variable(
            "RUN_LINTER",
            bool,
            "Enables the Verilator.Lint step and associated checker steps.",
            default=True,
            deprecated_names=["RUN_VERILATOR"],
        ),
        Variable(
            "QUIT_ON_LINTER_ERRORS",
            bool,
            "Quit immediately on any linter errors.",
            default=True,
            deprecated_names=["QUIT_ON_VERILATOR_ERRORS"],
        ),
        Variable(
            "QUIT_ON_LINTER_WARNINGS",
            bool,
            "Quit immediately on any linter warnings.",
            default=False,
            deprecated_names=["QUIT_ON_VERILATOR_WARNINGS"],
        ),
        Variable(
            "QUIT_ON_LINTER_TIMING_CONSTRUCTS",
            bool,
            "Quit immediately on any discovered timing constructs during linting.",
            default=True,
            deprecated_names=["QUIT_ON_LINTER_TIMING_CONSTRUCTS"],
        ),
        Variable(
            "RUN_TAP_ENDCAP_INSERTION",
            bool,
            "Enables the OpenROAD.TapEndcapInsertion step.",
            default=True,
            deprecated_names=["TAP_DECAP_INSERTION", "RUN_TAP_DECAP_INSERTION"],
        ),
        Variable(
            "RUN_REPAIR_DESIGN",
            bool,
            "Enables resizer design repair using the OpenROAD.RepairDesign step.",
            default=True,
            deprecated_names=["PL_RESIZER_DESIGN_OPTIMIZATIONS"],
        ),
        Variable(
            "RUN_CTS",
            bool,
            "Enables clock tree synthesis using the OpenROAD.CTS step.",
            default=True,
            deprecated_names=["CLOCK_TREE_SYNTH"],
        ),
        Variable(
            "RUN_POST_CTS_RESIZER_TIMING",
            bool,
            "Enables resizer timing optimizations after clock tree synthesis using the OpenROAD.ResizerTimingPostCTS step.",
            default=True,
            deprecated_names=["PL_RESIZER_TIMING_OPTIMIZATIONS"],
        ),
        Variable(
            "RUN_POST_GRT_RESIZER_TIMING",
            bool,
            "Enables resizer timing optimizations after global routing using the OpenROAD.ResizerTimingPostGRT step.",
            default=True,
            deprecated_names=["GLB_RESIZER_TIMING_OPTIMIZATIONS"],
        ),
        Variable(
            "RUN_HEURISTIC_DIODE_INSERTION",
            bool,
            "Enables the Odb.HeuristicDiodeInsertion step.",
            default=False,  # For compatibility with OL1
        ),
        Variable(
            "RUN_DRT",
            bool,
            "Enables the OpenROAD.DetailedRouting step.",
            default=True,
        ),
        Variable(
            "RUN_FILL_INSERTION",
            bool,
            "Enables the OpenROAD.FillInsertion step.",
            default=True,
        ),
        Variable(
            "RUN_MCSTA",
            bool,
            "Enables multi-corner static timing analysis using the OpenROAD.STAPostPNR step.",
            default=True,
            deprecated_names=["RUN_SPEF_STA"],
        ),
        Variable(
            "RUN_SPEF_EXTRACTION",
            bool,
            "Enables parasitics extraction using the OpenROAD.RCX step.",
            default=True,
        ),
        Variable(
            "RUN_IRDROP_REPORT",
            bool,
            "Enables generation of an IR Drop report using the OpenROAD.IRDropReport step.",
            default=True,
        ),
        Variable(
            "RUN_LVS",
            bool,
            "Enables the Netgen.LVS step.",
            default=True,
        ),
        Variable(
            "RUN_MAGIC_STREAMOUT",
            bool,
            "Enables the Magic.StreamOut step to generate GDSII.",
            default=True,
            deprecated_names=["RUN_MAGIC"],
        ),
        Variable(
            "RUN_KLAYOUT_STREAMOUT",
            bool,
            "Enables the KLayout.StreamOut step to generate GDSII.",
            default=True,
            deprecated_names=["RUN_KLAYOUT"],
        ),
        Variable(
            "RUN_MAGIC_WRITE_LEF",
            bool,
            "Enables the Magic.WriteLEF step.",
            default=True,
            deprecated_names=["MAGIC_GENERATE_LEF"],
        ),
        Variable(
            "RUN_KLAYOUT_XOR",
            bool,
            "Enables running the KLayout.XOR step on the two GDSII files generated by Magic and Klayout. Stream-outs for both KLayout and Magic should have already run, and the PDK must support both signoff tools.",
            default=True,
        ),
        Variable(
            "RUN_MAGIC_DRC",
            bool,
            "Enables the Magic.DRC step.",
            default=True,
        ),
        Variable(
            "RUN_EQY",
            bool,
            "Enables the Yosys.EQY step.",
            default=False,
        ),
        Variable(
            "QUIT_ON_UNMAPPED_CELLS",
            bool,
            "Checks for unmapped cells after synthesis and quits immediately if so.",
            deprecated_names=["CHECK_UNMAPPED_CELLS"],
            default=True,
        ),
        Variable(
            "QUIT_ON_SYNTH_CHECKS",
            bool,
            "Quits the flow immediately if one or more synthesis check errors are flagged. This checks for combinational loops and/or wires with no drivers.",
            default=True,
        ),
        Variable(
            "QUIT_ON_TR_DRC",
            bool,
            "Checks for DRC violations after routing and exits the flow if any was found.",
            default=True,
        ),
        Variable(
            "QUIT_ON_MAGIC_DRC",
            bool,
            "Checks for DRC violations after magic DRC is executed and exits the flow if any was found.",
            default=True,
        ),
        Variable(
            "QUIT_ON_DISCONNECTED_PINS",
            bool,
            "Checks for disconnected instance pins after detailed routing and quits immediately if so.",
            default=True,
        ),
        Variable(
            "QUIT_ON_LONG_WIRE",
            bool,
            "Checks if any wire length exceeds the threshold set in the PDK. If so, an error is raised at the end of the flow.",
            default=False,
        ),
        Variable(
            "QUIT_ON_XOR_ERROR",
            bool,
            "Checks for geometric differences between the Magic and KLayout stream-outs. If any exist, raise an error at the end of the flow.",
            default=True,
        ),
        Variable(
            "QUIT_ON_ILLEGAL_OVERLAPS",
            bool,
            "Checks for illegal overlaps during Magic extraction. In some cases, these imply existing undetected shorts in the design. It raises an error at the end of the flow if so.",
            default=True,
        ),
        Variable(
            "QUIT_ON_LVS_ERROR",
            bool,
            "Checks for LVS errors after Netgen is executed. If any exist, it raises an error at the end of the flow.",
            default=True,
        ),
    ]

    gating_config_vars = {
        "Verilator.Lint": ["RUN_LINTER"],
        "Checker.LintErrors": ["RUN_LINTER", "QUIT_ON_LINTER_ERRORS"],
        "Checker.LintWarnings": ["RUN_LINTER", "QUIT_ON_LINTER_WARNINGS"],
        "Checker.LintTimingConstructs": [
            "RUN_LINTER",
            "QUIT_ON_LINTER_TIMING_CONSTRUCTS",
        ],
        "OpenROAD.RepairDesign": ["RUN_REPAIR_DESIGN"],
        "OpenROAD.CTS": ["RUN_CTS"],
        "OpenROAD.ResizerTimingPostCTS": ["RUN_POST_CTS_RESIZER_TIMING"],
        "OpenROAD.RCX": ["RUN_SPEF_EXTRACTION"],
        "OpenROAD.TapEndcapInsertion": ["RUN_TAP_ENDCAP_INSERTION"],
        "OpenROAD.ResizerTimingPostGRT": ["RUN_POST_GRT_RESIZER_TIMING"],
        "Odb.HeuristicDiodeInsertion": ["RUN_HEURISTIC_DIODE_INSERTION"],
        "OpenROAD.DetailedRouting": ["RUN_DRT"],
        "OpenROAD.FillInsertion": ["RUN_FILL_INSERTION"],
        "OpenROAD.STAPostPNR": ["RUN_MCSTA"],
        "OpenROAD.IRDropReport": ["RUN_IRDROP_REPORT"],
        "Magic.StreamOut": ["RUN_MAGIC_STREAMOUT"],
        "KLayout.StreamOut": ["RUN_KLAYOUT_STREAMOUT"],
        "Magic.WriteLEF": ["RUN_MAGIC_WRITE_LEF"],
        "Magic.DRC": ["RUN_MAGIC_DRC"],
        "KLayout.XOR": [
            "RUN_KLAYOUT_XOR",
            "RUN_MAGIC_STREAMOUT",
            "RUN_KLAYOUT_STREAMOUT",
        ],
        "Netgen.LVS": ["RUN_LVS"],
        "Yosys.EQY": ["RUN_EQY"],
        "Checker.YosysUnmappedCells": ["QUIT_ON_UNMAPPED_CELLS"],
        "Checker.YosysChecks": ["QUIT_ON_SYNTH_CHECKS"],
        "Checker.TrDRC": ["RUN_DRT", "QUIT_ON_TR_DRC"],
        "Checker.MagicDRC": ["RUN_MAGIC_DRC", "QUIT_ON_MAGIC_DRC"],
        "Checker.DisconnectedPins": ["QUIT_ON_DISCONNECTED_PINS"],
        "Checker.WireLength": ["QUIT_ON_LONG_WIRE"],
        "Checker.XOR": [
            "QUIT_ON_XOR_ERROR",
            "RUN_KLAYOUT_XOR",
            "RUN_MAGIC_STREAMOUT",
            "RUN_KLAYOUT_STREAMOUT",
        ],
        "Checker.IllegalOverlap": ["QUIT_ON_ILLEGAL_OVERLAPS"],
        "Checker.LVS": ["RUN_LVS", "QUIT_ON_LVS_ERROR"],
        # "KLayout.DRC": Variable(
        #     "RUN_KLAYOUT_DRC",
        #     bool,
        #     "Enables running KLayout DRC on GDSII produced by magic.",
        #     default=False,
        # ),
    }
