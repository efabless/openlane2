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
import subprocess
import sys
from base64 import b64encode
from typing import Optional, List

from .step import Step, StepError, StepException
from ..logging import warn
from ..state import DesignFormat, State, Path
from ..config import Variable, Config
from ..common import get_script_dir
from ..utils import Toolbox


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


@Step.factory.register()
class StreamOut(Step):
    """
    Converts DEF views into GDSII streams using KLayout.

    The PDK must support KLayout for this step to work, otherwise
    it will be skipped.

    If ``PRIMARY_SIGNOFF_TOOL`` is set to ``"klayout"``, both GDS and KLAYOUT_GDS
    will be updated, and if set to another tool, only ``KLAYOUT_GDS`` will be
    updated.
    """

    id = "KLayout.StreamOut"
    name = "GDSII Stream Out (KLayout)"
    flow_control_variable = "RUN_KLAYOUT_STREAMOUT"

    inputs = [DesignFormat.DEF]
    outputs = [DesignFormat.GDS, DesignFormat.KLAYOUT_GDS]

    config_vars = [
        Variable(
            "RUN_KLAYOUT_STREAMOUT",
            bool,
            "Enables streaming GDSII using KLayout.",
            default=True,
            deprecated_names=["RUN_KLAYOUT"],
        )
    ]

    def run(self, state_in: State, **kwargs) -> State:
        state_out = super().run(state_in, **kwargs)

        lyp = self.config["KLAYOUT_PROPERTIES"]
        lyt = self.config["KLAYOUT_TECH"]
        lym = self.config["KLAYOUT_DEF_LAYER_MAP"]
        if None in [lyp, lyt, lym]:
            if self.config["PRIMARY_SIGNOFF_TOOL"].value == "klayout":
                raise StepError(
                    "One of KLAYOUT_PROPERTIES, KLAYOUT_TECH or KLAYOUT_DEF_LAYER_MAP is unset, yet, KLayout is set as the primary sign-off tool."
                )
            warn(
                "One of KLAYOUT_PROPERTIES, KLAYOUT_TECH or KLAYOUT_DEF_LAYER_MAP is unset. Returning state unaltered…"
            )
            return state_out

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

        state_out[DesignFormat.KLAYOUT_GDS] = Path(klayout_gds_out)

        if self.config["PRIMARY_SIGNOFF_TOOL"].value == "klayout":
            state_out[DesignFormat.GDS] = state_out[DesignFormat.KLAYOUT_GDS]

        return state_out

    def layout_preview(self) -> Optional[str]:
        if self.state_out is None:
            return None
        assert self.toolbox is not None

        if image := self.toolbox.render_png(
            self.config, str(self.state_out["klayout_gds"])
        ):
            image_encoded = b64encode(image).decode("utf8")
            return f'<img src="data:image/png;base64,{image_encoded}" />'

        return None


@Step.factory.register()
class XOR(Step):
    """
    Performs an XOR operation on the Magic and KLayout GDS views. The idea is:
    if there's any difference between the GDSII streams between the two tools,
    one of them have it wrong and that may lead to ambiguity.
    """

    id = "KLayout.XOR"
    name = "KLayout vs. Magic XOR"
    flow_control_variable = "RUN_KLAYOUT_XOR"

    inputs = [
        DesignFormat.MAG_GDS,
        DesignFormat.KLAYOUT_GDS,
    ]

    config_vars = [
        Variable(
            "RUN_KLAYOUT_XOR",
            bool,
            "Enables running KLayout XOR on the two GDSII files generated by Magic and Klayout. Stream-outs for both KLayout and Magic should have already run, and the PDK must support both signoff tools.",
            default=True,
        ),
        Variable(
            "KLAYOUT_XOR_THREADS",
            int,
            "Specifies number of threads used in the KLayout XOR check.",
            default=1,
        ),
    ]

    def run(self, state_in: State, **kwargs) -> State:
        state_out = super().run(state_in, **kwargs)

        ignored = ""
        if ignore_list := self.config["KLAYOUT_XOR_IGNORE_LAYERS"]:
            ignored = ";".join(ignore_list)

        layout_a = state_out[DesignFormat.MAG_GDS]
        if layout_a is None:
            warn("No Magic stream-out has been performed. Skipping XOR process…")
            return state_out
        layout_b = state_out[DesignFormat.KLAYOUT_GDS]
        if layout_b is None:
            warn("No KLayout stream-out has been performed. Skipping XOR process…")
            return state_out

        kwargs, env = self.extract_env(kwargs)

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
                "--ignore",
                ignored,
                layout_a,
                layout_b,
            ],
            env=env,
        )

        state_out.metrics["design__xor_difference__count"] = int(
            open(os.path.join(self.step_dir, "difference_count.rpt")).read().strip()
        )

        return state_out


@Step.factory.register()
class OpenGUI(Step):
    """
    Opens the DEF view in the KLayout GUI, with layers loaded and mapped
    properly. Useful to inspect ``.klayout.xml`` database files and the like.
    """

    id = "KLayout.OpenGUI"
    name = "Open In GUI"

    inputs = [DesignFormat.DEF]
    outputs = []

    def run(self, state_in: State, **kwargs) -> State:
        state_out = super().run(state_in, **kwargs)

        lyp = self.config["KLAYOUT_PROPERTIES"]
        lyt = self.config["KLAYOUT_TECH"]
        lym = self.config["KLAYOUT_DEF_LAYER_MAP"]
        if None in [lyp, lyt, lym]:
            raise StepError(
                "Cannot open design in KLayout as the PDK does not appear to support KLayout."
            )

        lefs = get_lef_args(self.config, self.toolbox)
        kwargs, env = self.extract_env(kwargs)

        cmd = [
            sys.executable,
            os.path.join(
                get_script_dir(),
                "klayout",
                "open_design.py",
            ),
            "--lyt",
            str(lyt),
            "--lyp",
            str(lyp),
            "--lym",
            str(lym),
            str(state_out.get("def")),
        ] + lefs

        print(" ".join(cmd))

        subprocess.check_call(
            cmd,
            env=env,
        )

        return state_out
