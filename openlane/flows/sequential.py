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

import os
import subprocess
from typing import List, Tuple, Optional, Type, Dict, Union

from .flow import Flow, FlowException, FlowError
from ..state import State
from ..steps import (
    Step,
    StepError,
    StepException,
    DeferredStepError,
)
from ..logging import info, success, err


class SequentialFlow(Flow):
    """
    The simplest Flow, running each Step as a stage, serially,
    with nothing happening in parallel and no significant inter-step
    processing.

    All subclasses of this flow have to do is override the :attr:`.Steps` abstract property
    and it would automatically handle the rest. See `Classic` in Built-in Flows for an example.

    :param Substitute: Substitute all instances of one `Step` type by another `Step`
        type in the :attr:`.Steps` attribute for this instance only.

        You may also use the string Step IDs in place of a `Step` type object.

    :param args: Arguments for :class:`Flow`.
    :param kwargs: Keyword arguments for :class:`Flow`.
    """

    @classmethod
    def make(Self, step_ids: List[str]) -> Type[SequentialFlow]:
        Step_list = []
        for name in step_ids:
            step = Step.get(name)
            if step is None:
                raise TypeError(f"No step found with id '{name}'")
            Step_list.append(step)

        class CustomSequentialFlow(SequentialFlow):
            name = "Custom Sequential Flow"
            Steps = Step_list

        return CustomSequentialFlow

    def __init__(
        self,
        *args,
        Substitute: Optional[
            Dict[str, Union[str, Type[Step]]],
        ] = None,
        **kwargs,
    ):
        self.Steps = self.Steps.copy()  # Break global reference

        if substitute := Substitute:
            for key, item in substitute.items():
                self._substitute_step(key, item)

        super().__init__(*args, **kwargs)

    def _substitute_step(
        self,
        id: str,
        with_step: Union[str, Type[Step]],
    ):
        if not isinstance(id, str):
            raise FlowException(
                "Keys in the 'Substitute' dictionary must be string IDs."
            )
        if with_step is None:
            raise FlowException(f"Invalid replacement step for {id}: 'None'")

        step_index: Optional[int] = None
        for i, step in enumerate(self.Steps):
            if step.id.lower() == id.lower():
                step_index = i
                break
        if step_index is None:
            raise FlowException(
                f"Failed to process start step '{step}': no step with ID '{step}' found in flow."
            )

        if isinstance(with_step, str):
            with_step_opt = Step.get(with_step)
            if with_step_opt is None:
                raise FlowException(
                    f"Could not substitute '{step.id}' with '{with_step}': no step with ID '{with_step}' found."
                )
            with_step = with_step_opt

        self.Steps[i] = with_step

    def run(
        self,
        initial_state: State,
        frm: Optional[str] = None,
        to: Optional[str] = None,
        skip: Optional[List[str]] = None,
        **kwargs,
    ) -> Tuple[State, List[Step]]:
        step_ids = {cls.id.lower(): cls.id for cls in reversed(self.Steps)}
        skipped_ids = []

        frm_resolved = None
        if frm is not None:
            if id := step_ids.get(frm.lower()):
                frm_resolved = id
            else:
                raise FlowException(
                    f"Failed to process start step '{frm}': no step with ID '{frm}' found in flow."
                )

        to_resolved = None
        if to is not None:
            if id := step_ids.get(to.lower()):
                to_resolved = id
            else:
                raise FlowException(
                    f"Failed to process start step '{to}': no step with ID '{to}' found in flow."
                )

        if skipped_steps := skip:
            for skipped_step in skipped_steps:
                if id := step_ids.get(skipped_step.lower()):
                    skipped_ids.append(id)
                else:
                    raise FlowException(
                        f"Failed to process skipped step '{skipped_step}': no step with ID '{skipped_step}' found in flow."
                    )
        step_count = len(self.Steps)
        self.set_max_stage_count(step_count)

        step_list = []

        info("Starting…")

        executing = frm is None
        deferred_errors = []

        current_state = initial_state
        for cls in self.Steps:
            step = cls(config=self.config, state_in=current_state, flow=self)
            if frm_resolved is not None and frm_resolved == step.id:
                executing = True

            self.start_stage(step.name)
            increment_ordinal = True
            if not executing or cls.id in skipped_ids:
                info(f"Skipping step '{step.name}'…")
                increment_ordinal = False
            else:
                step_list.append(step)
                try:
                    current_state = step.start()
                except StepException as e:
                    raise FlowException(str(e))
                except DeferredStepError as e:
                    deferred_errors.append(str(e))
                except (StepError, subprocess.CalledProcessError) as e:
                    raise FlowError(str(e))

            self.end_stage(increment_ordinal=increment_ordinal)

            if to_resolved and to_resolved == step.id:
                executing = False
        if len(deferred_errors) != 0:
            err("The following deferred step errors have been encountered:")
            for error in deferred_errors:
                err(error)
            raise FlowError("One or more deferred errors were encountered.")

        assert self.run_dir is not None
        final_views_path = os.path.join(self.run_dir, "final")
        info(f"Saving final views to '{final_views_path}'…")
        try:
            current_state.save_snapshot(final_views_path)
        except Exception as e:
            raise FlowException(f"Failed to save final views: {e}")
        success("Flow complete.")
        return (current_state, step_list)
