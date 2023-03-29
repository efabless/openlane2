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
from ..steps import (
    Step,
)
from ..steps import (
    Yosys,
    OpenROAD,
    Magic,
    Misc,
    KLayout,
    Odb,
    Netgen,
    Checker,
)
from .flow import Flow
from .sequential import SequentialFlow


@Flow.factory.register()
class Classic(SequentialFlow):
    """
    A flow of type :class:`openlane.flows.SequentialFlow` that is the most
    similar to the original OpenLane 1.0 flow, running the Verilog RTL through
    Yosys, OpenROAD, KLayout and Magic to produce a valid GDSII for simpler designs.

    This is the default when using OpenLane via the command-line.
    """

    Steps: List[Type[Step]] = [
        Yosys.Synthesis,
        Checker.YosysUnmappedCells,
        Misc.LoadBaseSDC,
        OpenROAD.NetlistSTA,
        OpenROAD.Floorplan,
        Odb.ManualMacroPlacement,
        Odb.ApplyDEFTemplate,
        OpenROAD.TapDecapInsertion,
        OpenROAD.IOPlacement,
        Odb.CustomIOPlacement,
        OpenROAD.GeneratePDN,
        OpenROAD.GlobalPlacement,
        Odb.DiodesOnPorts,
        Odb.HeuristicDiodeInsertion,
        OpenROAD.RepairDesign,
        OpenROAD.DetailedPlacement,
        OpenROAD.CTS,
        OpenROAD.ResizerTimingPostCTS,
        OpenROAD.GlobalRouting,
        OpenROAD.ResizerTimingPostGRT,
        OpenROAD.DetailedRouting,
        Checker.TrDRC,
        Odb.ReportWireLength,
        Checker.WireLength,
        OpenROAD.FillInsertion,
        OpenROAD.ParasiticsExtraction,
        OpenROAD.ParasiticsSTA,
        OpenROAD.IRDropReport,
        Magic.StreamOut,
        KLayout.StreamOut,
        KLayout.XOR,
        Magic.DRC,
        Checker.MagicDRC,
        Magic.SpiceExtraction,
        Checker.IllegalOverlap,
        Netgen.LVS,
        Checker.LVS,
    ]
