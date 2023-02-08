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
    Yosys,
    OpenROAD,
    Magic,
    Misc,
    KLayout,
    Odb,
    Netgen,
)
from .flow import Flow
from .sequential import SequentialFlow


@Flow.factory.register()
class Classic(SequentialFlow):
    """
    The flow most similar to the original Tcl-based OpenLane.
    """

    Steps: List[Type[Step]] = [
        Yosys.Synthesis,
        Misc.LoadBaseSDC,
        OpenROAD.NetlistSTA,
        OpenROAD.Floorplan,
        Odb.ManualMacroPlacement,
        OpenROAD.TapDecapInsertion,
        OpenROAD.GeneratePDN,
        OpenROAD.IOPlacement,
        OpenROAD.GlobalPlacement,
        OpenROAD.RepairDesign,
        OpenROAD.DetailedPlacement,
        OpenROAD.CTS,
        OpenROAD.ResizerTimingPostCTS,
        OpenROAD.GlobalRouting,
        OpenROAD.ResizerTimingPostGRT,
        # OpenROAD.CheckAntennae,
        OpenROAD.DetailedRouting,
        OpenROAD.FillInsertion,
        OpenROAD.ParasiticsExtraction,
        OpenROAD.ParasiticsSTA,
        OpenROAD.IRDropReport,
        Magic.StreamOut,
        KLayout.StreamOut,
        KLayout.XOR,
        Magic.DRC,
        Magic.SpiceExtraction,
        Netgen.LVS,
    ]
