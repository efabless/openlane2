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
from __future__ import annotations

import os
import subprocess
from typing import List, Tuple

from .flow import Flow
from ..common import get_script_dir
from ..steps import Step, State


@Flow.factory.register()
class OpenInKLayout(Flow):
    """
    This 'flow' actually just opens the LEF/DEF from the initial state object
    in KLayout. Fancy that.

    Intended for use with run tags that have already been run with
    another flow.
    """

    name = "Opening in KLayout"

    def run(
        self,
        initial_state: State,
        **kwargs,
    ) -> Tuple[List[State], List[Step]]:
        self.set_max_stage_count(1)
        self.start_stage("Opening in KLayout")

        lefs = []
        for lef in self.config["CELLS_LEF"]:
            lefs.append("--input-lef")
            lefs.append(lef)
        if extra_lefs := self.config["EXTRA_LEFS"]:
            for lef in extra_lefs:
                lefs.append("--input-lef")
                lefs.append(lef)

        subprocess.check_call(
            [
                "python3",
                os.path.join(
                    get_script_dir(),
                    "klayout",
                    "open_design.py",
                ),
                "--input-tlef",
                self.config["TECH_LEF"],
                "--tech-file",
                self.config["KLAYOUT_TECH"],
                "--props-file",
                self.config["KLAYOUT_PROPERTIES"],
                initial_state["def"],
            ]
            + lefs
        )
        self.end_stage()

        return ([], [])
