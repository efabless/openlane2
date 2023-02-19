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
from typing import List, Tuple
from concurrent.futures import Future

from .flow import Flow
from ..common import success, log, slugify
from ..steps import State, Step
from ..steps.builtins import Yosys, OpenROAD
from ..config import Config


@Flow.factory.register()
class Optimizing(Flow):
    """
    A customized flow composed of two stages:

    * The Synthesis Exploration - tries multiple synthesis strategies in *parallel*.

    The best-performing strategy in terms of minimizing the area makes it to the next stage.

    * Floorplanning and Placement - tries FP and placement with a high utilization.

    If the high utilization fails, a lower is fallen back to as a suggestion.
    """

    def run(
        self,
        initial_state: State,
        **kwargs,
    ) -> Tuple[List[State], List[Step]]:
        state_list = [initial_state]
        step_list: List[Step] = []

        self.set_max_stage_count(2)

        synthesis_futures: List[Tuple[Config, Future[State]]] = []
        self.start_stage("Synthesis Exploration")

        for strategy in ["AREA 0", "AREA 2", "DELAY 1"]:
            config = self.config.copy()
            config["SYNTH_STRATEGY"] = strategy

            synth_step = Yosys.Synthesis(
                config,
                id=slugify(f"Synthesis {strategy}"),
                silent=True,
            )
            synth_future = self.run_step_async(synth_step)
            step_list.append(synth_step)

            sta_step = OpenROAD.NetlistSTA(
                config,
                state_in=synth_future,
                id=slugify(f"STA {strategy}"),
                silent=True,
            )
            step_list.append(sta_step)
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

        log(f"Using result from '{min_strat}…")
        state_list.append(min_area_state)

        state_list_rewind = state_list.copy()

        self.start_stage("Floorplanning and Placement")

        fp_config = min_config.copy()
        fp_config["FP_CORE_UTIL"] = 99
        fp = OpenROAD.Floorplan(
            fp_config,
            id="fp_highutl",
            long_name="Floorplanning (High Util)",
        )
        step_list.append(fp)
        state_list.append(fp.start())
        try:
            io = OpenROAD.IOPlacement(
                fp_config,
                id="io-highutl",
                long_name="I/O Placement (High Util)",
            )
            step_list.append(io)
            state_list.append(io.start())
            gpl = OpenROAD.GlobalPlacement(
                fp_config,
                id="gpl-highutil",
                long_name="Global Placement (High Util)",
            )
            step_list.append(gpl)
            state_list.append(gpl.start())
        except subprocess.CalledProcessError:
            log("High utilization failed- attempting low utilization…")
            state_list = state_list_rewind
            fp_config = min_config.copy()
            fp_config["FP_CORE_UTIL"] = 40
            fp = OpenROAD.Floorplan(
                fp_config,
                id="fp-lowutl",
                long_name="Floorplanning (Low Util)",
            )
            step_list.append(fp)
            state_list.append(fp.start())
            io = OpenROAD.IOPlacement(
                fp_config,
                id="io-lowutl",
                long_name="I/O Placement (Low Util)",
            )
            step_list.append(io)
            state_list.append(io.start())
            gpl = OpenROAD.GlobalPlacement(
                fp_config,
                id="gpl-lowutl",
                long_name="Global Placement (Low Util)",
            )
            step_list.append(gpl)
            state_list.append(gpl.start())

        self.end_stage()

        success("Flow complete.")
        return (state_list, step_list)
