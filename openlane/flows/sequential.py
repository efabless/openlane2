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

from .flow import Flow, FlowException, FlowError
from ..state import State
from ..steps import (
    MissingInputError,
    Step,
    StepError,
    DeferredStepError,
)
from ..common import log, success, err


class SequentialFlow(Flow):
    """
    The simplest Flow, running each Step as a stage, serially,
    with nothing happening in parallel and no significant inter-step
    processing.

    All subclasses of this flow have to do is override the :attr:`.Steps` abstract property
    and it would automatically handle the rest. See `Classic` for an example.
    """

    @classmethod
    def make(Self, step_ids: List[str]) -> Type["SequentialFlow"]:
        step_list = []
        for name in step_ids:
            step = Step.get(name)
            if step is None:
                raise TypeError(f"No step found with id '{name}'")
            step_list.append(step)

        class CustomSequentialFlow(SequentialFlow):
            name = "Custom Sequential Flow"
            Steps = step_list

        return CustomSequentialFlow

    def run(
        self,
        initial_state: State,
        frm: Optional[str] = None,
        to: Optional[str] = None,
        **kwargs,
    ) -> Tuple[State, List[Step]]:
        frm_resolved = None
        to_resolved = None
        for cls in self.Steps:
            if frm is not None and frm.lower() == cls.id.lower():
                frm_resolved = cls.id
            if to is not None and to.lower() == cls.id.lower():
                to_resolved = cls.id

        if frm is not None and frm_resolved is None:
            raise FlowException(f"Failed to process end step '{frm}': step not found")
        if to is not None and to_resolved is None:
            raise FlowException(f"Failed to process end step '{to}': step not found")

        step_count = len(self.Steps)
        self.set_max_stage_count(step_count)

        step_list = []

        log("Starting…")

        executing = frm is None
        deferred_errors = []

        current_state = initial_state
        for cls in self.Steps:
            step = cls(config=self.config, state_in=current_state)
            if frm_resolved is not None and frm_resolved == step.id:
                executing = True

            self.start_stage(step.name)
            if not executing:
                log(f"Skipping step '{step.name}'…")
                self.end_stage(no_increment_ordinal=True)
                continue

            step_list.append(step)
            try:
                current_state = step.start()
            except MissingInputError as e:
                raise FlowException(str(e))
            except DeferredStepError as e:
                deferred_errors.append(str(e))
            except (StepError, subprocess.CalledProcessError) as e:
                raise FlowError(str(e))

            self.end_stage()

            if to_resolved and to_resolved == step.id:
                executing = False
        if len(deferred_errors) != 0:
            err("The following deferred step errors have been encountered:")
            for error in deferred_errors:
                err(error)
            raise FlowError("One or more deferred errors were encountered.")
        success("Flow complete.")
        return (current_state, step_list)
