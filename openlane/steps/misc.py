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
from typing import Optional, Tuple

from ..logging import info
from ..config import Variable
from ..state import State, DesignFormat
from ..common import Path, get_script_dir
from .step import ViewsUpdate, MetricsUpdate, Step


@Step.factory.register()
class LoadBaseSDC(Step):
    """
    Loads an SDC file specified as a configuration variable into the state
    object unaltered.
    """

    id = "Misc.LoadBaseSDC"
    name = "Load Base SDC"
    long_name = "Load Base Design Constraints File"

    inputs = []
    outputs = [DesignFormat.SDC]

    config_vars = [
        Variable(
            "BASE_SDC_FILE",
            Optional[Path],
            "Specifies the base SDC file to source before running Static Timing Analysis.",
            deprecated_names=["SDC_FILE"],
        ),
    ]

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        path = Path(
            os.path.join(
                get_script_dir(),
                "base.sdc",
            )
        )
        if self.config.get("BASE_SDC_FILE") is not None:
            info(f"Loading SDC file at '{self.config['BASE_SDC_FILE']}'.")
            path = self.config["BASE_SDC_FILE"]
        else:
            info("Loading default SDC file.")

        return {DesignFormat.SDC: path}, {}
