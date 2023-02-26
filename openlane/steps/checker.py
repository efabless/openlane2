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

from decimal import Decimal
from typing import Optional
from abc import abstractmethod

from .step import Step, DeferredStepError, State

from ..config import Variable
from ..common import err, warn, log


class MetricChecker(Step):
    @abstractmethod
    def get_metric_name(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get_metric_description(self) -> str:
        raise NotImplementedError()

    def get_threshold(self) -> Optional[Decimal]:
        return Decimal(0)

    def run(self, **kwargs) -> State:
        state_out = super().run()

        metric_name = self.get_metric_name()
        metric_description = self.get_metric_description()
        threshold = self.get_threshold()

        if threshold is None:
            warn(
                f"Threshold for {metric_description} is not set. The checker will be skipped."
            )
        else:
            metric_value = state_out.metrics.get(metric_name)
            if metric_value is not None:
                if metric_value > threshold:
                    error_msg = f"{metric_value} {metric_description} found."
                    err(f"{error_msg} - deferred")
                    raise DeferredStepError(error_msg)
                else:
                    log(f"Check for {metric_description} clear.")
            else:
                warn(
                    f"The {metric_description} metric was not found. Are you sure the relevant step was run?"
                )

        return state_out


@Step.factory.register("Checker.TrDRC")
class TrDRC(MetricChecker):
    flow_control_variable = "QUIT_ON_TR_DRC"
    name = "Routing DRC Checker"
    long_name = "Routing Design Rule Check"

    config_vars = [
        Variable(
            "QUIT_ON_TR_DRC",
            bool,
            "Checks for DRC violations after routing and exits the flow if any was found.",
            default=True,
        ),
    ]

    def get_metric_name(self) -> str:
        return "route__drc_errors"

    def get_metric_description(self) -> str:
        return "Routing DRC errors"


@Step.factory.register("Checker.MagicDRC")
class MagicDRC(MetricChecker):
    flow_control_variable = "QUIT_ON_MAGIC_DRC"
    name = "Magic DRC Checker"
    long_name = "Magic Design Rule Check"

    config_vars = [
        Variable(
            "QUIT_ON_MAGIC_DRC",
            bool,
            "Checks for DRC violations after magic DRC is executed and exits the flow if any was found.",
            default=True,
        ),
    ]

    def get_metric_name(self) -> str:
        return "magic__drc_errors"

    def get_metric_description(self) -> str:
        return "Magic DRC errors"


@Step.factory.register("Checker.IllegalOverlap")
class IllegalOverlap(MetricChecker):
    flow_control_variable = "QUIT_ON_ILLEGAL_OVERLAPS"
    name = "Illegal Overlap Checker"
    long_name = "Spice Extraction-based Illegal Overlap Check"

    config_vars = [
        Variable(
            "QUIT_ON_ILLEGAL_OVERLAPS",
            bool,
            "Checks for illegal overlaps during magic extraction. In some cases, these imply existing undetected shorts in the design. It also exits the flow if any was found.",
            default=True,
        ),
    ]

    def get_metric_name(self) -> str:
        return "magic__illegal__overlaps"

    def get_metric_description(self) -> str:
        return "Magic Illegal Overlap errors"


@Step.factory.register("Checker.WireLength")
class WireLength(MetricChecker):
    flow_control_variable = "QUIT_ON_LONG_WIRE"
    name = "Wire Length Threshold Checker"

    metric_name = "route__max__wirelength"
    metric_description = "Threshold-surpassing long wires"

    config_vars = [
        Variable(
            "QUIT_ON_LONG_WIRE",
            bool,
            "Exits the flow if any wire length exceeds the threshold set in the PDK.",
            default=False,
        ),
    ]

    def get_metric_name(self) -> str:
        return "route__max__wirelength"

    def get_metric_description(self) -> str:
        return "Threshold-surpassing long wires"

    def get_threshold(self) -> Optional[Decimal]:
        threshold = self.config["WIRE_LENGTH_THRESHOLD"]
        assert threshold is None or isinstance(threshold, Decimal)
        return threshold


@Step.factory.register("Checker.LVS")
class LVS(MetricChecker):
    flow_control_variable = "QUIT_ON_LVS_ERROR"
    name = "LVS Error Checker"
    long_name = "Layout vs. Schematic Error Checker"

    config_vars = [
        Variable(
            "QUIT_ON_LVS_ERROR",
            bool,
            "Checks for LVS errors after netgen LVS is executed and exits the flow if any was found.",
            default=True,
        ),
    ]

    def get_metric_name(self) -> str:
        return "lvs__total__errors"

    def get_metric_description(self) -> str:
        return "LVS errors"
