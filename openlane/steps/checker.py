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

from ..common import err, warn
from .state import State
from .step import Step, DeferredStepError


@Step.factory.register("Checker.TrDRC")
class TrDRC(Step):
    flow_control_variable = "QUIT_ON_TR_DRC"
    name = "OpenROAD DRC errors check"

    def run(
        self,
        **kwargs,
    ) -> State:
        state_out = super().run()
        if (drc_errors_count := state_out.metrics.get("route__drc_errors")) is None:
            warn(
                "No OpenROAD routing DRC errors reported. OpenROAD.DetailedRouting routing didn't run"
            )
        elif drc_errors_count > 0:
            error_msg = f"{drc_errors_count} OpenROAD routing DRC errors found."
            err(f"{error_msg} - deferred")
            raise DeferredStepError(error_msg)
        return state_out


@Step.factory.register("Checker.MagicDRC")
class MagicDRC(Step):
    flow_control_variable = "QUIT_ON_MAGIC_DRC"
    name = "Magic DRC errors check"

    def run(
        self,
        **kwargs,
    ) -> State:
        state_out = super().run()
        if (drc_errors_count := state_out.metrics.get("magic__drc_errors")) is None:
            warn("No Magic DRC errors reported. Magic.DRC didn't run")
        elif drc_errors_count > 0:
            error_msg = f"{drc_errors_count} Magic DRC errors found."
            err(f"{error_msg} - deferred")
            raise DeferredStepError(error_msg)
        return state_out


@Step.factory.register("Checker.IllegalOverlap")
class IllegalOverlap(Step):
    flow_control_variable = "QUIT_ON_ILLEGAL_OVERLAPS"
    name = "Spice extraction illegal overlap check"

    def run(
        self,
        **kwargs,
    ) -> State:

        state_out = super().run()
        if (
            illegal_overlaps := state_out.metrics.get("magic__illegal__overlaps")
        ) is None:
            warn("No illegal overlaps reported. Magic.SpiceExtraction didn't run")
        elif illegal_overlaps > 0:
            error_msg = f"{illegal_overlaps} illegal overlaps found during spice extraction."
            err(f"{error_msg} - deferred")
            raise DeferredStepError(error_msg)
        return state_out


@Step.factory.register("Checker.WireLength")
class WireLength(Step):
    flow_control_variable = "QUIT_ON_LONG_WIRE"
    name = "Max wire length check "

    def run(
        self,
        **kwargs,
    ) -> State:

        state_out = super().run()
        if (threshold := self.config["WIRE_LENGTH_THRESHOLD"]) is None:
            warn("WIRE_LENGTH_THRESHOLD not specified")
        elif (
            max_wire_length := state_out.metrics.get("route__max__wirelength")
        ) is None:
            warn("No max wirelength errors reported. Odb.ReportWireLength didn't run")
        elif max_wire_length > threshold:
            error_msg = f"Max wire length ({max_wire_length}) is larger than the threshold {threshold}"
            err(f"{error_msg} - deferred")
            raise DeferredStepError(error_msg)
        return state_out


@Step.factory.register("Checker.LVS")
class LVS(Step):
    flow_control_variable = "QUIT_ON_LVS_ERROR"
    name = "LVS errors check"

    def run(
        self,
        **kwargs,
    ) -> State:
        state_out = super().run()
        lvs_errors_count = state_out.metrics.get("lvs__total__errors")
        if lvs_errors_count is None:
            warn("No LVS errors reported. Netgen.LVS didn't run")
        elif lvs_errors_count > 0:
            error_msg = f"{lvs_errors_count} LVS errors found."
            err(f"{error_msg} - deferred")
            raise DeferredStepError(error_msg)
        return state_out
