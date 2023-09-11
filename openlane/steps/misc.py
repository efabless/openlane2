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
from typing import Tuple

from ..config.flow import option_variables
from ..logging import warn
from ..state import State, DesignFormat
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

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        path = self.config.get("BASE_SDC_FILE")
        default_sdc_file = next(
            iter([var for var in option_variables if var.name == "BASE_SDC_FILE"]), None
        )
        assert default_sdc_file is not None
        if path == default_sdc_file.default and (self.config.get("PNR_SDC_FILE") == None or self.config.get("SIGNOFF_SDC_FILE") == None):
            warn("BASE_SDC_FILE is not defined. Loading default SDC file")
        if self.config.get("PNR_SDC_FILE") == None:
            warn("PNR_SDC_FILE is not defined. Using default SDC file for PNR steps")
        if self.config.get("SIGNOFF_SDC_FILE") == None:
            warn(
                "SIGNOFF_SDC_FILE is not defined. Using default SDC file for signoff steps"
            )

        return {DesignFormat.SDC: path}, {}
