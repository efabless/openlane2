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
from abc import abstractmethod
from typing import List, Optional

from .step import Step
from .tclstep import TclStep
from ..state import DesignFormat, State

from ..config import Variable
from ..common import get_script_dir
from ..utils import DRC as DRCObject


class MagicStep(TclStep):
    inputs = [DesignFormat.GDS]
    outputs = []

    config_vars = [
        Variable(
            "MAGIC_DEF_LABELS",
            bool,
            "A flag to choose whether labels are read with DEF files or not. From magic docs: \"The '-labels' option to the 'def read' command causes each net in the NETS and SPECIALNETS sections of the DEF file to be annotated with a label having the net name as the label text.\"",
            default=True,
        ),
        Variable(
            "MAGIC_GDS_POLYGON_SUBCELLS",
            bool,
            'A flag to enable polygon subcells in magic for gds read potentially speeding up magic. From magic docs: "Put non-Manhattan polygons. This prevents interations with other polygons on the same plane and so reduces tile splitting."',
            default=False,
        ),
        Variable(
            "MAGIC_GDS_ALLOW_ABSTRACT",
            bool,
            "A flag to allow abstract view of macros when processing GDS files in Magic.",
            default=False,
        ),
        Variable(
            "MAGIC_DEF_NO_BLOCKAGES",
            bool,
            "If set to true, blockages in DEF files are ignored. Otherwise, they are read as sheets of metal by Magic.",
            default=True,
        ),
        Variable(
            "MAGIC_INCLUDE_GDS_POINTERS",
            bool,
            "A flag to choose whether to include GDS pointers in the generated mag files or not.",
            default=False,
        ),
    ]

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

    def run(self, state_in: State, **kwargs) -> State:
        # https://github.com/RTimothyEdwards/magic/issues/218
        kwargs, env = self.extract_env(kwargs)
        kwargs["stdin"] = open(
            os.path.join(get_script_dir(), "magic", "wrapper.tcl"), encoding="utf8"
        )
        env["MAGIC_SCRIPT"] = self.get_script_path()

        env["MACRO_GDS_FILES"] = ""
        for gds in self.toolbox.get_macro_views(self.config, DesignFormat.GDS):
            env["MACRO_GDS_FILES"] += f" {gds}"
        return super().run(state_in, env=env, **kwargs)


@Step.factory.register()
class WriteLEF(MagicStep):
    """
    Writes a LEF view of the design using the GDS using Magic.
    """

    id = "Magic.WriteLEF"
    name = "Write LEF (Magic)"
    flow_control_variable = "RUN_MAGIC_WRITE_LEF"

    inputs = [DesignFormat.GDS, DesignFormat.DEF]
    outputs = [DesignFormat.LEF]

    config_vars = MagicStep.config_vars + [
        Variable(
            "RUN_MAGIC_WRITE_LEF",
            bool,
            "Generate a LEF view using Magic.",
            default=True,
            deprecated_names=["MAGIC_GENERATE_LEF"],
        ),
        Variable(
            "MAGIC_LEF_WRITE_USE_GDS",
            bool,
            "A flag to choose whether to use GDS for spice extraction or not. If not, then the extraction will be done using the DEF/LEF, which is faster.",
            default=True,
        ),
        Variable(
            "MAGIC_WRITE_FULL_LEF",
            bool,
            "A flag to specify whether or not the output LEF should include all shapes inside the macro or an abstracted view of the macro lef view via magic.",
            default=False,
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "magic", "lef.tcl")


@Step.factory.register()
class StreamOut(MagicStep):
    """
    Converts DEF views into GDSII streams using Magic.

    If ``PRIMARY_SIGNOFF_TOOL`` is set to ``"magic"``, both GDS and MAG_GDS
    will be updated, and if set to another tool, only ``MAG_GDS`` will be
    updated.
    """

    id = "Magic.StreamOut"
    name = "GDSII Stream Out (Magic)"
    flow_control_variable = "RUN_MAGIC_STREAMOUT"

    inputs = [DesignFormat.DEF]
    outputs = [DesignFormat.GDS, DesignFormat.MAG_GDS]

    config_vars = MagicStep.config_vars + [
        Variable(
            "RUN_MAGIC_STREAMOUT",
            bool,
            "Enables running GDSII streaming out using Magic.",
            default=True,
            deprecated_names=["RUN_MAGIC"],
        ),
        Variable(
            "DIE_AREA",
            Optional[str],
            'Specific die area to be used in floorplanning when `FP_SIZING` is set to `absolute`. Specified as a 4-corner rectangle "x0 y0 x1 y1".',
            units="μm",
        ),
        Variable(
            "MAGIC_ZEROIZE_ORIGIN",
            bool,
            "A flag to move the layout such that it's origin in the lef generated by magic is 0,0.",
            default=False,
        ),
        Variable(
            "MAGIC_DISABLE_CIF_INFO",
            bool,
            "A flag to disable writing Caltech Intermediate Format (CIF) hierarchy and subcell array information to the GDSII file.",
            default=True,
            deprecated_names=["MAGIC_DISABLE_HIER_GDS"],
        ),
        # Variable(
        #     "MAGIC_GDS_FLATTEN",
        #     bool,
        #     "todo",
        #     default=True,
        # ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "magic", "def", "mag_gds.tcl")

    def run(self, state_in: State, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        if diea_area := state_in.metrics.get("design__die__bbox"):
            env["DIE_AREA"] = diea_area

        state_out = super().run(state_in, env=env, **kwargs)
        if self.config["PRIMARY_SIGNOFF_TOOL"].value == "magic":
            state_out[DesignFormat.GDS] = state_out[DesignFormat.MAG_GDS]
        return state_out


@Step.factory.register()
class DRC(MagicStep):
    """
    Performs `design rule checking <https://en.wikipedia.org/wiki/Design_rule_checking>`_
    on the GDSII stream using Magic.

    This also converts the results to a KLayout database, which can be loaded.

    The metrics will be updated with ``magic__drc_errors``. You can use
    `the relevant checker <#Checker.MagicDRC>`_ to quit if that number is
    nonzero.
    """

    id = "Magic.DRC"
    name = "DRC"
    long_name = "Design Rule Checks"

    flow_control_variable = "RUN_MAGIC_DRC"

    inputs = [DesignFormat.DEF, DesignFormat.GDS]
    outputs = []

    config_vars = [
        Variable(
            "RUN_MAGIC_DRC",
            bool,
            "Enables running magic DRC on GDSII produced by Magic.",
            default=True,
        ),
        Variable(
            "MAGIC_DRC_USE_GDS",
            bool,
            "A flag to choose whether to run the magic DRC checks on GDS or not. If not, then the checks will be done on the DEF/LEF, which is faster.",
            default=False,
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "magic", "drc.tcl")

    def run(self, state_in: State, **kwargs) -> State:
        state_out = super().run(state_in, **kwargs)

        reports_dir = os.path.join(self.step_dir, "reports")
        report_path = os.path.join(reports_dir, "drc.rpt")
        report_stats = os.stat(report_path)

        drc_db_file = None
        if report_stats.st_size >= 0:  # 134217728:
            drc_db_file = os.path.join(reports_dir, "drc.db")

        drc, bbox_count = DRCObject.from_magic(
            open(report_path, encoding="utf8"),
            db_file=drc_db_file,
        )
        state_out.metrics["magic__drc_errors"] = bbox_count

        klayout_db_path = os.path.join(reports_dir, "drc.klayout.xml")
        drc.to_klayout_xml(open(klayout_db_path, "wb"))

        return state_out


@Step.factory.register()
class SpiceExtraction(MagicStep):
    """
    Extracts a SPICE netlist from the GDSII stream. Used in Layout vs. Schematic
    checks.

    Also, the metrics will be updated with ``magic__illegal__overlaps``. You can use
    `the relevant checker <#Checker.IllegalOverlap>`_ to quit if that number is
    nonzero.
    """

    id = "Magic.SpiceExtraction"
    name = "SPICE Extraction"
    long_name = "SPICE Model Extraction"

    inputs = [DesignFormat.GDS, DesignFormat.DEF]
    outputs = [DesignFormat.SPICE]

    config_vars = MagicStep.config_vars + [
        Variable(
            "MAGIC_EXT_USE_GDS",
            bool,
            "A flag to choose whether to use GDS for spice extraction or not. If not, then the extraction will be done using the DEF/LEF, which is faster.",
            default=False,
        ),
        Variable(
            "MAGIC_NO_EXT_UNIQUE",
            bool,
            "Enables connections by label in LVS by skipping `extract unique` in Magic extractions.",
            default=False,
            deprecated_names=["LVS_CONNECT_BY_LABEL"],
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "magic", "extract_spice.tcl")

    def run(self, state_in: State, **kwargs) -> State:
        state_out = super().run(state_in, **kwargs)

        feedback_path = os.path.join(self.step_dir, "feedback.txt")
        feedback_string = open(feedback_path, encoding="utf8").read()
        state_out.metrics["magic__illegal__overlaps"] = feedback_string.count(
            "Illegal overlap"
        )
        return state_out
