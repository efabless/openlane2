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
import math
import subprocess
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor

from rich.progress import Progress

from .flow import Flow, FlowFactory
from ..steps import State, Yosys, OpenROAD
from ..common import success, log


class Optimizing(Flow):
    def run(
        self,
        p: Progress,
        run_dir: str,
        with_initial_state: Optional[State] = None,
    ) -> Tuple[bool, List[State]]:
        flow_name = self.get_name()
        step_count = 1

        initial_state = with_initial_state or State()
        state_list = [initial_state]

        p.log("Starting…")
        task_id = p.add_task(f"{flow_name}", total=step_count)
        i = 1
        synthesis_states = []
        with ThreadPoolExecutor(4, "optimizing_flow") as tpe:
            synthesis_futures = []
            p.update(
                task_id,
                description=f"{flow_name} - Step {i} - Synthesis Exploration",
            )
            log("Starting Synthesis exploration…")
            for strategy in ["AREA 0", "AREA 2", "DELAY 1"]:

                def metastep1(strategy, config):
                    synth_step = Yosys.Synthesis(
                        config,
                        state_in=initial_state,
                        run_dir=run_dir,
                        prefix=self.prefix(i),
                        name=f"Synthesis {strategy}",
                        silent=True,
                    )
                    mid_state = synth_step.start()
                    sta_step = OpenROAD.NetlistSTA(
                        config,
                        state_in=mid_state,
                        run_dir=run_dir,
                        prefix=self.prefix(i),
                        name=f"STA {strategy}",
                        silent=True,
                    )
                    return (strategy, config, sta_step.start())

                config = self.config_in.copy()
                config["SYNTH_STRATEGY"] = strategy
                synthesis_futures.append(tpe.submit(metastep1, strategy, config))
            synthesis_states = [future.result() for future in synthesis_futures]
            p.update(task_id, completed=1)

            min_config = None
            min_area_state = None
            min_strat = None
            min_area = math.inf
            for strategy, config, state in synthesis_states:
                area = state.metrics["design__instance__area"]
                log(f"Strategy: {strategy}")
                log(f"Area: {area}")
                if area < min_area:
                    min_area_state = state
                    min_strat = strategy
                    min_area = area
                    min_config = config

            log(f"Using result from '{min_strat}'...")
            state_list.append(min_area_state)

            i += 1

            i_rewind = i
            state_list_rewind = state_list.copy()

            fp_config = min_config.copy()
            fp_config["FP_CORE_UTIL"] = 80
            fp = OpenROAD.Floorplan(
                fp_config,
                state_in=state_list[-1],
                run_dir=run_dir,
                prefix=self.prefix(i),
                name="Floorplanning (High Util)",
            )
            state_list.append(fp.start())
            i += 1
            io = OpenROAD.IOPlacement(
                fp_config,
                state_in=state_list[-1],
                run_dir=run_dir,
                prefix=self.prefix(i),
                name="I/O Placement (High Util)",
            )
            state_list.append(io.start())
            try:
                i += 1
                gpl = OpenROAD.GlobalPlacement(
                    fp_config,
                    state_in=state_list[-1],
                    run_dir=run_dir,
                    prefix=self.prefix(i),
                    name="Global Placement (High Util)",
                )
                state_list.append(gpl.start())
            except subprocess.CalledProcessError:
                log("High utilization failed- attempting low utilization...")
                i = i_rewind
                state_list = state_list_rewind
                fp_config = min_config.copy()
                fp_config["FP_CORE_UTIL"] = 40
                fp = OpenROAD.Floorplan(
                    fp_config,
                    state_in=state_list[-1],
                    run_dir=run_dir,
                    prefix=self.prefix(i),
                    name="Floorplanning (Low Util)",
                )
                state_list.append(fp.start())
                io = OpenROAD.IOPlacement(
                    fp_config,
                    state_in=state_list[-1],
                    run_dir=run_dir,
                    prefix=self.prefix(i),
                    name="I/O Placement (High Util)",
                )
                state_list.append(io.start())
                gpl = OpenROAD.GlobalPlacement(
                    fp_config,
                    state_in=state_list[-1],
                    run_dir=run_dir,
                    prefix=self.prefix(i),
                    name="Global Placement (Low Util)",
                )
                state_list.append(gpl.start())

        success("Flow complete.")
        return (True, state_list)


FlowFactory.register(Optimizing)
