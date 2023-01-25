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
import json
from typing import List
from abc import abstractmethod

from .step import Step
from .state import DesignFormat, State
from ..common import get_script_dir, log


class LoadBaseSDC(Step):
    name = "Load Base SDC"
    long_name = "Load Base Design Constraints File"

    outputs = [DesignFormat.SDC]

    def run(self, **kwargs) -> State:
        new_state = super().run(**kwargs)
        new_state[DesignFormat.SDC] = os.path.join(
            get_script_dir(),
            "base.sdc",
        )
        if self.config.get("BASE_SDC_PATH") is not None:
            log(f"Loaded SDC file at '{config['BASE_SDC_PATH']}'.")
            new_state[DesignFormat.SDC] = config["BASE_SDC_PATH"]
        else:
            log(f"Loaded default SDC file.")

        return new_state
