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
from typing import Tuple

from .step import ViewsUpdate, MetricsUpdate, Step
from ..common import Path
from ..state import State, DesignFormat


@Step.factory.register()
class LoadBaseSDC(Step):
    """
    Loads an SDC file specified as a configuration variable into the state
    object unaltered.

    This Step exists for legacy compatibility and should not be used
    in new flows.
    """

    id = "Misc.LoadBaseSDC"
    name = "Load Base SDC"
    long_name = "Load Base Design Constraints File"

    inputs = []
    outputs = [DesignFormat.SDC]

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        path = self.config["FALLBACK_SDC_FILE"]

        target = os.path.join(self.step_dir, f"{self.config['DESIGN_NAME']}.sdc")

        # Otherwise, you'll end up with weird permissions and may have to chmod
        with open(target, "w", encoding="utf8") as out:
            for line in open(path, "r", encoding="utf8"):
                out.write(line)

        return {DesignFormat.SDC: Path(target)}, {}
