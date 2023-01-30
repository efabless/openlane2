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
import glob
from typing import List
from abc import abstractmethod

from .tclstep import TclStep
from .state import DesignFormat, State


class NetgenStep(TclStep):
    inputs = []
    outputs = []

    @abstractmethod
    def get_script_path(self):
        pass

    def get_command(self) -> List[str]:
        return ["netgen", "-batch", "source"]


class LVS(NetgenStep):
    inputs = [DesignFormat.SPICE, DesignFormat.POWERED_NETLIST]

    def get_command(self) -> List[str]:
        return super().get_command() + [self.get_script_path()]

    def get_script_path(self):
        return os.path.join(self.step_dir, "script.lvs")

    def run(self, **kwargs) -> State:
        assert isinstance(self.state_in, State)
        spice_glob = os.path.join(
            self.config["PDK_ROOT"],
            self.config["PDK"],
            "libs.ref",
            self.config["STD_CELL_LIBRARY"],
            "spice",
            "*.spice",
        )
        spice_files: List[str] = glob.glob(spice_glob)

        if pdk_spice_files := self.config.get("SPICE_MODELS"):
            spice_files = pdk_spice_files.copy()

        if extra_spice_files := self.config.get("EXTRA_SPICE_MODELS"):
            spice_files += extra_spice_files

        design_name = self.config["DESIGN_NAME"]

        with open(self.get_script_path(), "w") as f:
            for lib in spice_files:
                print(
                    f"puts \"Reading SPICE netlist file '{lib}'...\"",
                    file=f,
                )
                print(
                    f"readnet spice {lib} 1",
                    file=f,
                )

            print(
                f"lvs {{ {self.state_in[DesignFormat.SPICE]} {design_name} }} {{ {self.state_in[DesignFormat.POWERED_NETLIST]} {design_name} }} {self.config['NETGEN_SETUP']} {os.path.abspath(self.step_dir)}/lvs.rpt -json",
                file=f,
            )
        return super().run(**kwargs)
