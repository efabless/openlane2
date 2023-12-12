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
import json
import os
import shlex
import sys
import site
import shutil
import subprocess
from base64 import b64encode
from typing import Any, Dict, Optional, List, Sequence, Tuple, Union

from .step import ViewsUpdate, MetricsUpdate, Step, StepError, StepException

from ..logging import info, warn
from ..config import Variable, Config
from ..state import DesignFormat, State
from ..common import Path, get_script_dir, Toolbox


def get_lef_args(config: Config, toolbox: Toolbox) -> List[str]:
    tech_lefs = toolbox.filter_views(config, config["TECH_LEFS"])
    if len(tech_lefs) != 1:
        raise StepException(
            "Misconfigured SCL: 'TECH_LEFS' must return exactly one Tech LEF for its default timing corner."
        )

    lef_args = [
        "--input-lef",
        str(tech_lefs[0]),
    ]

    for lef in config["CELL_LEFS"]:
        lef_args.append("--input-lef")
        lef_args.append(str(lef))

    macro_lefs = toolbox.get_macro_views(config, DesignFormat.LEF)
    for lef in macro_lefs:
        lef_args.append("--input-lef")
        lef_args.append(str(lef))

    if extra_lefs := config["EXTRA_LEFS"]:
        for lef in extra_lefs:
            lef_args.append("--input-lef")
            lef_args.append(str(lef))

    return lef_args


class KLayoutStep(Step):
    config_vars = [
        Variable(
            "KLAYOUT_TECH",
            Path,
            "A path to the KLayout layer technology (.lyt) file.",
            pdk=True,
        ),
        Variable(
            "KLAYOUT_PROPERTIES",
            Path,
            "A path to the KLayout layer properties (.lyp) file.",
            pdk=True,
        ),
        Variable(
            "KLAYOUT_DEF_LAYER_MAP",
            Path,
            "A path to the KLayout LEF/DEF layer mapping (.map) file.",
            pdk=True,
        ),
    ]

    def run_subprocess(
        self,
        cmd: Sequence[Union[str, os.PathLike]],
        log_to: Optional[Union[str, os.PathLike]] = None,
        silent: bool = False,
        report_dir: Optional[Union[str, os.PathLike]] = None,
        env: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        env = env or os.environ.copy()
        # Hack for Python subprocesses to get access to installed libraries
        python_path_elements = site.getsitepackages()
        if current_pythonpath := env.get("PYTHONPATH"):
            python_path_elements.append(current_pythonpath)

        env["PYTHONPATH"] = ":".join(python_path_elements)
        return super().run_subprocess(cmd, log_to, silent, report_dir, env, **kwargs)


@Step.factory.register()
class Render(KLayoutStep):
    """
    Renders a PNG of the layout using KLayout.

    DEF is required as an input, but if a GDS-II view
    exists in the input state, it will be used instead.
    """

    id = "KLayout.Render"
    name = "Render Image (w/ KLayout)"

    inputs = [DesignFormat.DEF]
    outputs = []

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        input_view = state_in[DesignFormat.DEF]
        if gds := state_in[DesignFormat.GDS]:
            input_view = gds

        lyp = self.config["KLAYOUT_PROPERTIES"]
        lyt = self.config["KLAYOUT_TECH"]
        lym = self.config["KLAYOUT_DEF_LAYER_MAP"]

        tech_lefs = self.toolbox.filter_views(self.config, self.config["TECH_LEFS"])
        if len(tech_lefs) != 1:
            raise StepError(
                "Misconfigured SCL: 'TECH_LEFS' must return exactly one Tech LEF for its default timing corner."
            )

        lef_arguments = ["-l", str(tech_lefs[0])]
        for file in self.config["CELL_LEFS"]:
            lef_arguments += ["-l", str(file)]
        if extra := self.config["EXTRA_LEFS"]:
            for file in extra:
                lef_arguments += ["-l", str(file)]

        self.run_subprocess(
            [
                sys.executable,
                os.path.join(get_script_dir(), "klayout", "render.py"),
                input_view,
                "--output",
                os.path.join(self.step_dir, "out.png"),
                "--lyp",
                lyp,
                "--lyt",
                lyt,
                "--lym",
                lym,
            ]
            + lef_arguments,
            silent=True,
        )

        return {}, {}


@Step.factory.register()
class StreamOut(KLayoutStep):
    """
    Converts DEF views into GDSII streams using KLayout.

    The PDK must support KLayout for this step to work, otherwise
    it will be skipped.

    If ``PRIMARY_GDSII_STREAMOUT_TOOL`` is set to ``"klayout"``, both GDS and KLAYOUT_GDS
    will be updated, and if set to another tool, only ``KLAYOUT_GDS`` will be
    updated.
    """

    id = "KLayout.StreamOut"
    name = "GDSII Stream Out (KLayout)"

    inputs = [DesignFormat.DEF]
    outputs = [DesignFormat.GDS, DesignFormat.KLAYOUT_GDS]

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        lyp = self.config["KLAYOUT_PROPERTIES"]
        lyt = self.config["KLAYOUT_TECH"]
        lym = self.config["KLAYOUT_DEF_LAYER_MAP"]
        if None in [lyp, lyt, lym]:
            if self.config["PRIMARY_GDSII_STREAMOUT_TOOL"] == "klayout":
                raise StepError(
                    "One of KLAYOUT_PROPERTIES, KLAYOUT_TECH or KLAYOUT_DEF_LAYER_MAP is unset, yet, KLayout is set as the primary sign-off tool."
                )
            warn(
                "One of KLAYOUT_PROPERTIES, KLAYOUT_TECH or KLAYOUT_DEF_LAYER_MAP is unset. Returning state unaltered…"
            )
            return {}, {}

        views_updates: ViewsUpdate = {}

        klayout_gds_out = os.path.join(
            self.step_dir,
            f"{self.config['DESIGN_NAME']}.{DesignFormat.KLAYOUT_GDS.value.extension}",
        )

        layout_args = []
        layout_args += get_lef_args(self.config, self.toolbox)

        for gds in self.config["CELL_GDS"]:
            layout_args.append("--with-gds-file")
            layout_args.append(gds)
        for gds in self.toolbox.get_macro_views(self.config, DesignFormat.GDS):
            layout_args.append("--with-gds-file")
            layout_args.append(gds)
        if extra_gds := self.config["EXTRA_GDS_FILES"]:
            for gds in extra_gds:
                layout_args.append("--with-gds-file")
                layout_args.append(gds)

        kwargs, env = self.extract_env(kwargs)

        self.run_subprocess(
            [
                sys.executable,
                os.path.join(
                    get_script_dir(),
                    "klayout",
                    "stream_out.py",
                ),
                state_in[DesignFormat.DEF.value.id],
                "--output",
                klayout_gds_out,
                "--lyt",
                lyt,
                "--lyp",
                lyp,
                "--lym",
                lym,
                "--top",
                self.config["DESIGN_NAME"],
            ]
            + layout_args,
            env=env,
        )

        views_updates[DesignFormat.KLAYOUT_GDS] = Path(klayout_gds_out)

        if self.config["PRIMARY_GDSII_STREAMOUT_TOOL"] == "klayout":
            gds_path = os.path.join(self.step_dir, f"{self.config['DESIGN_NAME']}.gds")
            shutil.copy(klayout_gds_out, gds_path)
            views_updates[DesignFormat.GDS] = Path(gds_path)

        return views_updates, {}

    def layout_preview(self) -> Optional[str]:
        if self.state_out is None:
            return None
        assert self.toolbox is not None

        if image := self.toolbox.render_png(self.config, self.state_out):
            image_encoded = b64encode(image).decode("utf8")
            return f'<img src="data:image/png;base64,{image_encoded}" />'

        return None


@Step.factory.register()
class XOR(KLayoutStep):
    """
    Performs an XOR operation on the Magic and KLayout GDS views. The idea is:
    if there's any difference between the GDSII streams between the two tools,
    one of them have it wrong and that may lead to ambiguity.
    """

    id = "KLayout.XOR"
    name = "KLayout vs. Magic XOR"

    inputs = [
        DesignFormat.MAG_GDS,
        DesignFormat.KLAYOUT_GDS,
    ]
    outputs = []

    config_vars = KLayoutStep.config_vars + [
        Variable(
            "KLAYOUT_XOR_THREADS",
            Optional[int],
            "Specifies number of threads used in the KLayout XOR check. If unset, this will be equal to your machine's thread count.",
        ),
        Variable(
            "KLAYOUT_XOR_IGNORE_LAYERS",
            Optional[List[str]],
            "KLayout layers to ignore during XOR operations.",
            pdk=True,
        ),
        Variable(
            "KLAYOUT_XOR_TILE_SIZE",
            Optional[int],
            "A tile size for the XOR process in µm.",
            pdk=True,
        ),
    ]

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        ignored = ""
        if ignore_list := self.config["KLAYOUT_XOR_IGNORE_LAYERS"]:
            ignored = ";".join(ignore_list)

        layout_a = state_in[DesignFormat.MAG_GDS]
        if layout_a is None:
            warn("No Magic stream-out has been performed. Skipping XOR process…")
            return {}, {}
        layout_b = state_in[DesignFormat.KLAYOUT_GDS]
        if layout_b is None:
            warn("No KLayout stream-out has been performed. Skipping XOR process…")
            return {}, {}

        kwargs, env = self.extract_env(kwargs)

        tile_size_options = []
        if tile_size := self.config["KLAYOUT_XOR_TILE_SIZE"]:
            tile_size_options += ["--tile-size", str(tile_size)]

        thread_count = self.config["KLAYOUT_XOR_THREADS"] or os.cpu_count() or 1
        info(f"Running XOR with {thread_count} threads…")

        self.run_subprocess(
            [
                "ruby",
                os.path.join(
                    get_script_dir(),
                    "klayout",
                    "xor.drc",
                ),
                "--output",
                os.path.join(self.step_dir, "xor.xml"),
                "--top",
                self.config["DESIGN_NAME"],
                "--threads",
                thread_count,
                "--ignore",
                ignored,
                layout_a,
                layout_b,
            ]
            + tile_size_options,
            env=env,
        )

        difference_count = int(
            open(os.path.join(self.step_dir, "difference_count.rpt")).read().strip()
        )

        return {}, {"design__xor_difference__count": difference_count}


@Step.factory.register()
class DRC(KLayoutStep):
    id = "KLayout.DRC"
    name = "Design Rule Check (KLayout)"

    inputs = [
        DesignFormat.GDS,
    ]
    outputs = []

    config_vars = KLayoutStep.config_vars + [
        Variable(
            "KLAYOUT_DRC_RUNSET",
            Optional[Path],
            "A path to KLayout DRC runset.",
            pdk=True,
            deprecated_names=["KLAYOUT_DRC_TECH_SCRIPT"],
        ),
        Variable(
            "KLAYOUT_DRC_OPTIONS",
            Optional[Dict[str, Union[bool, int]]],
            "Options availble to KLayout DRC runset. They vary from one PDK to another.",
            pdk=True,
        ),
        Variable(
            "KLAYOUT_DRC_THREADS",
            Optional[int],
            "Specifies the number of threads to be used in KLayout DRC"
            + "If unset, this will be equal to your machine's thread count.",
        ),
    ]

    def run_sky130(self, state_in: State, **kwargs) -> MetricsUpdate:
        metrics_updates: MetricsUpdate = {}
        drc_script_path = self.config["KLAYOUT_DRC_RUNSET"]
        kwargs, env = self.extract_env(kwargs)
        xml_report = os.path.join(self.step_dir, "violations.xml")
        json_report = os.path.join(self.step_dir, "violations.json")
        feol = str(self.config["KLAYOUT_DRC_OPTIONS"]["feol"]).lower()
        beol = str(self.config["KLAYOUT_DRC_OPTIONS"]["beol"]).lower()
        floating_metal = str(
            self.config["KLAYOUT_DRC_OPTIONS"]["floating_metal"]
        ).lower()
        offgrid = str(self.config["KLAYOUT_DRC_OPTIONS"]["offgrid"]).lower()
        seal = str(self.config["KLAYOUT_DRC_OPTIONS"]["seal"]).lower()
        threads = self.config["KLAYOUT_DRC_THREADS"] or (str(os.cpu_count()) or "1")
        info(f"Running KLayout DRC with {threads} threads…")

        self.run_subprocess(
            [
                "klayout",
                "-b",
                "-zz",
                "-r",
                drc_script_path,
                "-rd",
                f"input={str(state_in[DesignFormat.GDS])}",
                "-rd",
                f"topcell={str(self.config['DESIGN_NAME'])}",
                "-rd",
                f"report={xml_report}",
                "-rd",
                f"feol={feol}",
                "-rd",
                f"beol={beol}",
                "-rd",
                f"floating_metal={floating_metal}",
                "-rd",
                f"offgrid={offgrid}",
                "-rd",
                f"seal={seal}",
                "-rd",
                f"threads={threads}",
            ],
            env=env,
        )
        self.run_subprocess(
            [
                "python3",
                os.path.join(
                    get_script_dir(),
                    "klayout",
                    "xml_drc_report_to_json.py",
                ),
                f"--xml-file={xml_report}",
                f"--json-file={json_report}",
            ],
            env=env,
            log_to=os.path.join(self.step_dir, "xml_drc_report_to_json.log"),
        )

        with open(json_report, "r") as f:
            metrics_updates["klayout__drc_error__count"] = json.load(f)["total"]
        return metrics_updates

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        metrics_updates: MetricsUpdate = {}
        if self.config["PDK"] in ["sky130A", "sky130B"]:
            metrics_updates = self.run_sky130(state_in, **kwargs)
        else:
            warn(
                f"KLayout DRC is not supported for the {self.config['PDK']} PDK. This step will be skipped."
            )

        return {}, metrics_updates


@Step.factory.register()
class OpenGUI(KLayoutStep):
    """
    Opens the DEF view in the KLayout GUI, with layers loaded and mapped
    properly. Useful to inspect ``.klayout.xml`` database files and the like.
    """

    id = "KLayout.OpenGUI"
    name = "Open In GUI"

    inputs = [DesignFormat.DEF]
    outputs = []

    config_vars = KLayoutStep.config_vars + [
        Variable(
            "EDITOR_MODE",
            bool,
            "Whether to run the KLayout GUI in editor mode or in viewer mode.",
            default=False,
        )
    ]

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        lyp = self.config["KLAYOUT_PROPERTIES"]
        lyt = self.config["KLAYOUT_TECH"]
        lym = self.config["KLAYOUT_DEF_LAYER_MAP"]
        if None in [lyp, lyt, lym]:
            raise StepError(
                "Cannot open design in KLayout as the PDK does not appear to support KLayout."
            )

        lefs = get_lef_args(self.config, self.toolbox)
        kwargs, env = self.extract_env(kwargs)

        mode_arg = "--viewer"
        if self.config["EDITOR_MODE"]:
            mode_arg = "--editor"

        env["KLAYOUT_ARGV"] = shlex.join(
            [
                "--lyt",
                str(lyt),
                "--lyp",
                str(lyp),
                "--lym",
                str(lym),
                str(state_in[DesignFormat.DEF]),
            ]
            + lefs
        )

        cmd = [
            shutil.which("klayout") or "klayout",
            mode_arg,
            "-rm",
            os.path.join(
                get_script_dir(),
                "klayout",
                "open_design.py",
            ),
        ]

        subprocess.check_call(
            cmd,
            env=env,
        )

        return {}, {}
