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
from typing import List
from abc import abstractmethod

from .step import TclStep, get_script_dir
from .state import DesignFormat, State


class MagicStep(TclStep):
    inputs = [DesignFormat.GDSII]
    outputs = []

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
            self.get_script_path(),
        ]


class StreamOut(MagicStep):
    name = "GDS-II Stream Out"

    inputs = [DesignFormat.DEF]
    outputs = [
        DesignFormat.GDSII,
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "magic", "def", "mag_gds.tcl")


class DRC(MagicStep):
    name = "DRC"
    long_name = "Design Rule Checks"

    inputs = [DesignFormat.GDSII]
    outputs = []

    def get_script_path(self):
        return os.path.join(get_script_dir(), "magic", "drc.tcl")

    def run(self, **kwargs) -> State:
        kwargs, env = self.extract_env(kwargs)
        env["MAGIC_DRC_USE_GDS"] = "1"
        return super().run(**kwargs)
