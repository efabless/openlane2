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
from typing import Optional
from base64 import b64encode

from .step import Step, StepError
from ..state import DesignFormat, State

from ..logging import warn
from ..config import Path, Variable
from ..common import get_script_dir


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

    def run(self, **kwargs) -> State:
        state_out = super().run(**kwargs)

        assert isinstance(self.state_in, State)

        lyp = self.config["KLAYOUT_PROPERTIES"]
        lyt = self.config["KLAYOUT_TECH"]
        lym = self.config["KLAYOUT_DEF_LAYER_MAP"]
        if None in [lyp, lyt, lym]:
            if self.config["PRIMARY_SIGNOFF_TOOL"].value == "klayout":
                raise StepError(
                    "One of KLAYOUT_PROPERTIES, KLAYOUT_TECH or KLAYOUT_DEF_LAYER_MAP is unset, yet, KLayout is set as the primary sign-off tool."
                )
            warn(
                "One of KLAYOUT_PROPERTIES, KLAYOUT_TECH or KLAYOUT_DEF_LAYER_MAP is unset. Skipping KLayout stream-out…"
            )
            return state_out

        klayout_gds_out = os.path.join(
            self.step_dir,
            f"{self.config['DESIGN_NAME']}.{DesignFormat.KLAYOUT_GDS.value.extension}",
        )

        layout_args = [
            "--input-lef",
            self.config["TECH_LEFS"]["nom"],
        ]
        for lef in self.config["CELL_LEFS"]:
            layout_args.append("--input-lef")
            layout_args.append(lef)
        if extra_lefs := self.config["EXTRA_LEFS"]:
            for lef in extra_lefs:
                layout_args.append("--input-lef")
                layout_args.append(lef)
        for gds in self.config["CELL_GDS"]:
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
                self.state_in[DesignFormat.DEF.value.id],
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

    def run(self, **kwargs) -> State:
        state_out = super().run(**kwargs)

        ignored = ""
        if ignore_list := self.config["KLAYOUT_XOR_IGNORE_LAYERS"]:
            ignored = ";".join(ignore_list)

        layout_a = state_out[DesignFormat.MAG_GDS]
        if layout_a is None:
            warn("No Magic stream-out has been performed. Skipping XOR…")
            return state_out
        layout_b = state_out[DesignFormat.KLAYOUT_GDS]
        if layout_b is None:
            warn("No KLayout stream-out has been performed. Skipping XOR…")
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

    def run(self, **kwargs) -> State:
        state_out = super().run(**kwargs)

        assert isinstance(self.state_in, State)

        lyp = self.config["KLAYOUT_PROPERTIES"]
        lyt = self.config["KLAYOUT_TECH"]
        lym = self.config["KLAYOUT_DEF_LAYER_MAP"]
        if None in [lyp, lyt, lym]:
            raise StepError(
                "Cannot open design in KLayout as the PDK does not appear to support KLayout."
            )

        lefs = [
            "--input-lef",
            str(self.config["TECH_LEF"]),
        ]
        for lef in self.config["CELL_LEFS"]:
            lefs.append("--input-lef")
            lefs.append(str(lef))
        if extra_lefs := self.config["EXTRA_LEFS"]:
            for lef in extra_lefs:
                lefs.append("--input-lef")
                lefs.append(str(lef))

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
            str(self.state_in.get("def")),
        ] + lefs

        print(" ".join(cmd))

        subprocess.check_call(
            cmd,
            env=env,
        )

        return state_out
