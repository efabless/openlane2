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
import platform
import subprocess
from typing import Dict

from .step import Step, StepError
from .state import DesignFormat, State

from ..config import Path
from ..common import get_script_dir, warn

def patch_klayout_mac(env: Dict[str, str]) -> Dict[str, str]:
    """
    Hack until KLayout is rebuilt: with the reasoning is redoing the
    KLayout derivation takes about 8 years
    """
    klayout_path = subprocess.check_output([
        "which",
        "klayout"
    ]).decode('utf8')
    klayout_lib_path = os.path.join(
        os.path.dirname(os.path.dirname(klayout_path)),
        "lib"
    )

    env_out = env.copy()
    env_out["DYLD_LIBRARY_PATH"] = f"{klayout_lib_path}:{env_out.get('DYLD_LIBRARY_PATH', '')}"
    return env_out


@Step.factory.register("KLayout.StreamOut")
class StreamOut(Step):
    id = "klayout-streamout"
    name = "GDS-II Stream Out (KLayout)"
    flow_control_variable = "RUN_KLAYOUT_STREAMOUT"

    inputs = [DesignFormat.DEF]
    outputs = [DesignFormat.GDS, DesignFormat.KLAYOUT_GDS]

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
            f"{self.config['DESIGN_NAME']}.{DesignFormat.KLAYOUT_GDS.value[1]}",
        )

        layout_args = []
        for lef in self.config["CELLS_LEF"]:
            layout_args.append("--input-lef")
            layout_args.append(lef)
        if extra_lefs := self.config["EXTRA_LEFS"]:
            for lef in extra_lefs:
                layout_args.append("--input-lef")
                layout_args.append(lef)
        for gds in self.config["CELLS_GDS"]:
            layout_args.append("--with-gds-file")
            layout_args.append(gds)
        if extra_gds := self.config["EXTRA_GDS_FILES"]:
            for gds in extra_gds:
                layout_args.append("--with-gds-file")
                layout_args.append(gds)

        kwargs, env = self.extract_env(kwargs)
        if platform.system() == "Darwin":
            env = patch_klayout_mac(env)

        self.run_subprocess(
            [
                "python3",
                os.path.join(
                    get_script_dir(),
                    "klayout",
                    "stream_out.py",
                ),
                self.state_in[DesignFormat.DEF.value[0]],
                "--output",
                klayout_gds_out,
                "--tech-file",
                lyt,
                "--props-file",
                lyp,
                "--def-layer-map-file",
                lym,
                "--input-tlef",
                self.config["TECH_LEF"],
                "--top",
                self.config["DESIGN_NAME"],
            ]
            + layout_args,
            log_to=os.path.join(self.step_dir, "stream-out.log"),
            env=env,
        )

        state_out[DesignFormat.KLAYOUT_GDS] = Path(klayout_gds_out)

        if self.config["PRIMARY_SIGNOFF_TOOL"].value == "klayout":
            state_out[DesignFormat.GDS] = state_out[DesignFormat.KLAYOUT_GDS]

        return state_out


@Step.factory.register("KLayout.XOR")
class XOR(Step):
    id = "klayout-xor"
    name = "KLayout vs. Magic XOR"
    flow_control_variable = "RUN_KLAYOUT_XOR"

    inputs = [
        DesignFormat.MAG_GDS,
        DesignFormat.KLAYOUT_GDS,
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
        if platform.system() == "Darwin":
            env = patch_klayout_mac(env)

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
            log_to=os.path.join(self.step_dir, "xor.log"),
            env=env,
        )

        return state_out
