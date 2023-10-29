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
import shutil
from abc import abstractmethod
from typing import Literal, List, Optional, Tuple
from decimal import Decimal

from .step import StepError, StepException, ViewsUpdate, MetricsUpdate, Step
from .tclstep import TclStep
from ..state import DesignFormat, State

from ..config import Variable
from ..common import get_script_dir, DRC as DRCObject, Path


class MagicStep(TclStep):
    inputs = [DesignFormat.GDS]
    outputs = []

    config_vars = [
        Variable(
            "MAGIC_DEF_LABELS",
            bool,
            "A flag to choose whether labels are read with DEF files or not. From magic docs: \"The '-labels' option to the 'def read' command causes each net in the NETS and SPECIALNETS sections of the DEF file to be annotated with a label having the net name as the label text.\" If LVS fails, try disabling this option.",
            default=True,
        ),
        Variable(
            "MAGIC_GDS_POLYGON_SUBCELLS",
            bool,
            'A flag to enable polygon subcells in magic for gds read potentially speeding up magic. From magic docs: "Put non-Manhattan polygons. This prevents interations with other polygons on the same plane and so reduces tile splitting."',
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
        Variable(
            "MAGICRC",
            Path,
            "A path to the `.magicrc` file which is sourced before running magic in the flow.",
            deprecated_names=["MAGIC_MAGICRC"],
            pdk=True,
        ),
        Variable(
            "MAGIC_TECH",
            Path,
            "A path to a Magic tech file which, mainly, has DRC rules.",
            deprecated_names=["MAGIC_TECH_FILE"],
            pdk=True,
        ),
        Variable(
            "MAGIC_PDK_SETUP",
            Path,
            "A path to a PDK-specific setup file sourced by `.magicrc`.",
            pdk=True,
        ),
        Variable(
            "CELL_MAGS",
            Optional[List[Path]],
            "A list of pre-processed concrete views for cells. Read as a fallback for undefined cells.",
            pdk=True,
        ),
        Variable(
            "CELL_MAGLEFS",
            Optional[List[Path]],
            "A list of pre-processed abstract LEF views for cells. Read as a fallback for undefined cells in scripts where cells are blackboxed.",
            pdk=True,
        ),
        Variable(
            "MAGIC_CAPTURE_ERRORS",
            bool,
            "Capture errors print by Magic and quit when a fatal error is encountered."
            + " Fatal errors are determined heuristically. It is not guaranteed that they are fatal errors."
            + " Hence this is function is gated by a variable."
            + " This function is needed because Magic does not throw errors.",
            default=True,
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

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        # https://github.com/RTimothyEdwards/magic/issues/218
        kwargs, env = self.extract_env(kwargs)
        kwargs["stdin"] = open(
            os.path.join(get_script_dir(), "magic", "wrapper.tcl"), encoding="utf8"
        )
        env["MAGIC_SCRIPT"] = self.get_script_path()

        env["MACRO_GDS_FILES"] = ""
        for gds in self.toolbox.get_macro_views(self.config, DesignFormat.GDS):
            env["MACRO_GDS_FILES"] += f" {gds}"

        views_updates, metrics_updates = super().run(
            state_in,
            env=env,
            **kwargs,
        )

        if self.config["MAGIC_CAPTURE_ERRORS"]:
            error_patterns = [
                r"DEF read.*\(Error\).*",
                r"LEF read.*\(Error\).*",
                r"Error while reading cell(?!.*Warning:).*",
                r".*Calma output error.*",
                r".*is an abstract view.*",
            ]

            error_found = False
            for line in open(self.get_log_path(), encoding="utf8"):
                for pattern in error_patterns:
                    if re.match(pattern, line):
                        error_found = True
                        break
                if error_found is True:
                    raise StepError(
                        f"Error encountered during running Magic.\nError: {line}Check the log file of {self.id}."
                    )

        return views_updates, metrics_updates


@Step.factory.register()
class WriteLEF(MagicStep):
    """
    Writes a LEF view of the design using the GDS using Magic.
    """

    id = "Magic.WriteLEF"
    name = "Write LEF (Magic)"

    inputs = [DesignFormat.GDS, DesignFormat.DEF]
    outputs = [DesignFormat.LEF]

    config_vars = MagicStep.config_vars + [
        Variable(
            "MAGIC_LEF_WRITE_USE_GDS",
            bool,
            "A flag to choose whether to use GDS for LEF writing. If not, then the extraction will be done using the DEF/LEF with concrete views.",
            default=False,
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

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        kwargs, env = self.extract_env(kwargs)
        env["MAGTYPE"] = "mag"
        return super().run(state_in, **kwargs)


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

    inputs = [DesignFormat.DEF]
    outputs = [DesignFormat.GDS, DesignFormat.MAG_GDS, DesignFormat.MAG]

    config_vars = MagicStep.config_vars + [
        Variable(
            "DIE_AREA",
            Optional[Tuple[Decimal, Decimal, Decimal, Decimal]],
            'Specific die area to be used in floorplanning when `FP_SIZING` is set to `absolute`. Specified as a 4-corner rectangle "x0 y0 x1 y1".',
            units="µm",
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
        Variable(
            "MAGIC_MACRO_STD_CELL_SOURCE",
            Literal["PDK", "macro"],
            "If set to PDK, magic will use the PDK definition of the STD cells for macros inside the design."
            + " Otherwise, the macro is completely treated as a blackbox and magic will use the existing cell definition inside"
            + " the macro gds."
            + " This mode is only supported for macros specified in MACROS variable",
            default="macro",
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "magic", "def", "mag_gds.tcl")

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        kwargs, env = self.extract_env(kwargs)
        if die_area := state_in.metrics.get("design__die__bbox"):
            env["DIE_AREA"] = die_area

        env["MAGTYPE"] = "mag"

        if self.config["MACROS"] is not None:
            macro_gds = []
            for macro in self.config["MACROS"].keys():
                macro_gds.append(macro)
                macro_gds += [str(path) for path in self.config["MACROS"][macro].gds]
                macro_gds += ","
            from ..common import TclUtils

            env["__MACRO_GDS"] = TclUtils.join(macro_gds[:-1])

        views_updates, metrics_updates = super().run(
            state_in,
            env=env,
            **kwargs,
        )

        if self.config["PRIMARY_SIGNOFF_TOOL"] == "magic":
            magic_gds_out = str(views_updates[DesignFormat.MAG_GDS])
            gds_path = os.path.join(self.step_dir, f"{self.config['DESIGN_NAME']}.gds")
            shutil.copy(magic_gds_out, gds_path)
            views_updates[DesignFormat.GDS] = Path(gds_path)

        views_updates[DesignFormat.MAG] = Path(
            os.path.join(self.step_dir, f"{self.config['DESIGN_NAME']}.mag")
        )

        return views_updates, metrics_updates


@Step.factory.register()
class DRC(MagicStep):
    """
    Performs `design rule checking <https://en.wikipedia.org/wiki/Design_rule_checking>`_
    on the GDSII stream using Magic.

    This also converts the results to a KLayout database, which can be loaded.

    The metrics will be updated with ``magic__drc_error__count``. You can use
    `the relevant checker <#Checker.MagicDRC>`_ to quit if that number is
    nonzero.
    """

    id = "Magic.DRC"
    name = "DRC"
    long_name = "Design Rule Checks"

    inputs = [DesignFormat.DEF, DesignFormat.GDS]
    outputs = []

    config_vars = MagicStep.config_vars + [
        Variable(
            "MAGIC_DRC_USE_GDS",
            bool,
            "A flag to choose whether to run the Magic DRC checks on GDS or not. If not, then the checks will be done on the DEF view of the design, which is a bit faster, but may be less accurate as some DEF/LEF elements are abstract.",
            default=True,
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "magic", "drc.tcl")

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        views_updates, metrics_updates = super().run(state_in, **kwargs)

        reports_dir = os.path.join(self.step_dir, "reports")
        report_path = os.path.join(reports_dir, "drc.rpt")

        # report_stats = os.stat(report_path)
        # drc_db_file = None
        # if report_stats.st_size >= 0:  # 134217728:
        #     drc_db_file = os.path.join(reports_dir, "drc.db")

        drc, bbox_count = DRCObject.from_magic(
            open(report_path, encoding="utf8"),
            # db_file=drc_db_file,
        )

        klayout_db_path = os.path.join(reports_dir, "drc.klayout.xml")
        drc.to_klayout_xml(open(klayout_db_path, "wb"))

        metrics_updates["magic__drc_error__count"] = bbox_count

        return views_updates, metrics_updates


@Step.factory.register()
class SpiceExtraction(MagicStep):
    """
    Extracts a SPICE netlist from the GDSII stream. Used in Layout vs. Schematic
    checks.

    Also, the metrics will be updated with ``magic__illegal_overlap__count``. You can use
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
        Variable(
            "MAGIC_EXT_SHORT_RESISTOR",
            bool,
            "Enables adding resistors to shorts- resolves LVS issues if more than one top-level pin is connected to the same net, but may increase runtime and break some designs. Proceed with caution.",
            default=False,
        ),
        Variable(
            "MAGIC_EXT_ABSTRACT",
            bool,
            "Extracts a SPICE netlist based on black-boxed standard cells and macros (basically, anything with a LEF) rather than transistors. An error will be thrown if both this and `MAGIC_EXT_USE_GDS` is set to ``True``.",
            default=False,
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "magic", "extract_spice.tcl")

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        if self.config["MAGIC_EXT_USE_GDS"] and self.config["MAGIC_EXT_ABSTRACT"]:
            raise StepException(
                "'MAGIC_EXT_USE_GDS' and 'MAGIC_EXT_ABSTRACT' cannot be both set to 'True'. The step cannot run."
            )

        kwargs, env = self.extract_env(kwargs)

        env["MAGTYPE"] = "maglef" if self.config["MAGIC_EXT_ABSTRACT"] else "mag"

        views_updates, metrics_updates = super().run(state_in, env=env, **kwargs)

        feedback_path = os.path.join(self.step_dir, "feedback.txt")
        feedback_string = open(feedback_path, encoding="utf8").read()
        metrics_updates["magic__illegal_overlap__count"] = feedback_string.count(
            "Illegal overlap"
        )

        return views_updates, metrics_updates
