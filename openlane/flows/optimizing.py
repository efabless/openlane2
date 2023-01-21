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

import subprocess
from typing import List, Tuple, Optional
from concurrent.futures import Future

from .flow import Flow, FlowFactory
from ..common import success, log
from ..steps import State, Yosys, OpenROAD
from ..config import Config


class Optimizing(Flow):
    def run(
        self,
        with_initial_state: Optional[State] = None,
    ) -> Tuple[bool, List[State]]:
        initial_state = with_initial_state or State()
        state_list = [initial_state]
        self.set_stage_count(2)

        synthesis_futures: List[Tuple[Config, Future[State]]] = []
        log
        self.start_stage("Synthesis Exploration")

        for strategy in ["AREA 0", "AREA 2", "DELAY 1"]:
            config = self.config_in.copy()
            config["SYNTH_STRATEGY"] = strategy

            synth_step = Yosys.Synthesis(
                config,
                name=f"Synthesis {strategy}",
                silent=True,
            )
            synth_future = self.run_step_async(synth_step)

            sta_step = OpenROAD.NetlistSTA(
                config,
                state_in=synth_future,
                name=f"STA {strategy}",
                silent=True,
            )
            sta_future = self.run_step_async(sta_step)

            synthesis_futures.append((config, sta_future))

        synthesis_states: List[Tuple[Config, State]] = [
            (config, future.result()) for config, future in synthesis_futures
        ]
        self.end_stage()

        min_strat = synthesis_states[0][0]["SYNTH_STRATEGY"]
        min_config = synthesis_states[0][0]
        min_area_state = synthesis_states[0][1]
        for config, state in synthesis_states[1:]:
            strategy = config["SYNTH_STRATEGY"]
            if (
                state.metrics["design__instance__area"]
                < min_area_state.metrics["design__instance__area"]
            ):
                min_area_state = state
                min_strat = strategy
                min_config = config

        log(f"Using result from '{min_strat}'...")
        state_list.append(min_area_state)

        state_list_rewind = state_list.copy()

        self.start_stage("Floorplanning and Placement")

        fp_config = min_config.copy()
        fp_config["FP_CORE_UTIL"] = 99
        fp = OpenROAD.Floorplan(
            fp_config,
            name="Floorplanning (High Util)",
        )
        state_list.append(fp.start())
        try:
            io = OpenROAD.IOPlacement(
                fp_config,
                name="I/O Placement (High Util)",
            )
            state_list.append(io.start())
            gpl = OpenROAD.GlobalPlacement(
                fp_config,
                name="Global Placement (High Util)",
            )
            state_list.append(gpl.start())
        except subprocess.CalledProcessError:
            log("High utilization failed- attempting low utilization...")
            state_list = state_list_rewind
            fp_config = min_config.copy()
            fp_config["FP_CORE_UTIL"] = 40
            fp = OpenROAD.Floorplan(
                fp_config,
                name="Floorplanning (Low Util)",
            )
            state_list.append(fp.start())
            io = OpenROAD.IOPlacement(
                fp_config,
                name="I/O Placement (Low Util)",
            )
            state_list.append(io.start())
            gpl = OpenROAD.GlobalPlacement(
                fp_config,
                name="Global Placement (Low Util)",
            )
            state_list.append(gpl.start())

        self.end_stage()

        success("Flow complete.")
        return (True, state_list)


FlowFactory.register(Optimizing)
