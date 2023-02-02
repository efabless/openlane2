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
from typing import List, Tuple, Optional, Type

from .flow import Flow
from ..steps import (
    MissingInputError,
    State,
    Step,
)
from ..common import err, log, success


class SequentialFlow(Flow):
    """
    The simplest Flow, running each Step as a stage, serially,
    with nothing happening in parallel and no significant inter-step
    processing.

    All subclasses of this flow have to do is override the `Steps` property
    and it would automatically handle the rest. See `Classic` for an example.
    """

    @classmethod
    def make(Self, step_ids: List[str]) -> Type["SequentialFlow"]:
        step_list = []
        for name in step_ids:
            step = Step.factory.get(name)
            if step is None:
                raise TypeError(f"No step found with id '{name}'")
            step_list.append(step)

        class CustomSequentialFlow(SequentialFlow):
            name = "Custom Sequential Flow"
            Steps = step_list

        return CustomSequentialFlow

    def run(
        self,
        with_initial_state: Optional[State] = None,
    ) -> Tuple[bool, List[State]]:
        step_count = len(self.Steps)
        self.set_max_stage_count(step_count)

        initial_state = with_initial_state or State()
        state_list = [initial_state]
        log("Starting…")
        for cls in self.Steps:
            step = cls()
            self.steps.append(step)
            self.start_stage(step.name)
            try:
                new_state = step.start()
            except MissingInputError as e:
                err(f"Misconfigured flow: {e}")
                return (False, state_list)
            except subprocess.CalledProcessError:
                err("An error has been encountered. The flow will stop.")
                return (False, state_list)
            state_list.append(new_state)
            self.end_stage()
        success("Flow complete.")
        return (True, state_list)
