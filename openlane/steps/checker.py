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

from typing import ClassVar, Tuple
from decimal import Decimal
from typing import Optional

from .step import ViewsUpdate, MetricsUpdate, Step, StepError, DeferredStepError, State

from ..config import Variable
from ..logging import err, warn, info


class MetricChecker(Step):
    """
    Raises a (deferred) error if a Decimal metric exceeds a ccertain threshold.
    """

    inputs = []
    outputs = []

    metric_name: ClassVar[str] = NotImplemented
    metric_description: ClassVar[str] = NotImplemented
    deferred: ClassVar[bool] = True

    @classmethod
    def get_help_md(Self):
        threshold_string = Self.get_threshold_description(None)
        if threshold_string is None:
            threshold_string = str(Self.get_threshold(None))
        dynamic_docstring = "Raises"
        if Self.deferred:
            dynamic_docstring += " a deferred error"
        else:
            dynamic_docstring += " an immediate error"
        dynamic_docstring += f" if {Self.metric_description} (metric: ``{Self.metric_name}``) are >= {threshold_string}."

        return super().get_help_md(dynamic_docstring)

    def get_threshold(self: Optional["MetricChecker"]) -> Optional[Decimal]:
        return Decimal(0)

    def get_threshold_description(self: Optional["MetricChecker"]) -> Optional[str]:
        return None

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        threshold = self.get_threshold()

        if threshold is None:
            warn(
                f"Threshold for {self.metric_description} is not set. The checker will be skipped."
            )
        else:
            metric_value = state_in.metrics.get(self.metric_name)
            if metric_value is not None:
                if metric_value > threshold:
                    error_msg = f"{metric_value} {self.metric_description} found."
                    if self.deferred:
                        err(f"{error_msg} - deferred")
                        raise DeferredStepError(error_msg)
                    else:
                        err(f"{error_msg}")
                        raise StepError(error_msg)

                else:
                    info(f"Check for {self.metric_description} clear.")
            else:
                warn(
                    f"The {self.metric_description} metric was not found. Are you sure the relevant step was run?"
                )

        return {}, {}


@Step.factory.register()
class YosysUnmappedCells(MetricChecker):
    id = "Checker.YosysUnmappedCells"
    flow_control_variable = "QUIT_ON_UNMAPPED_CELLS"
    name = "Unmapped Cells Checker"
    deferred = False

    metric_name = "design__instance_unmapped__count"
    metric_description = "Unmapped Yosys instances"

    config_vars = [
        Variable(
            "QUIT_ON_UNMAPPED_CELLS",
            bool,
            "Checks for unmapped cells after synthesis.",
            deprecated_names=["CHECK_UNMAPPED_CELLS"],
            default=True,
        ),
    ]


@Step.factory.register()
class YosysSynthChecks(MetricChecker):
    id = "Checker.YosysChecks"
    flow_control_variable = "QUIT_ON_SYNTH_CHECKS"
    name = "Yosys Synth Checks"
    deferred = False

    metric_name = "synthesis__check_error__count"
    metric_description = "Yosys check errors"

    config_vars = [
        Variable(
            "QUIT_ON_SYNTH_CHECKS",
            bool,
            "Quits the flow if one or more synthesis check errors are flagged. This checks for combinational loops and/or wires with no drivers.",
            default=True,
        ),
    ]


@Step.factory.register()
class TrDRC(MetricChecker):
    id = "Checker.TrDRC"
    flow_control_variable = "QUIT_ON_TR_DRC"
    name = "Routing DRC Checker"
    long_name = "Routing Design Rule Checker"

    metric_name = "route__drc_errors"
    metric_description = "Routing DRC errors"

    config_vars = [
        Variable(
            "QUIT_ON_TR_DRC",
            bool,
            "Checks for DRC violations after routing and exits the flow if any was found.",
            default=True,
        ),
    ]


@Step.factory.register()
class MagicDRC(MetricChecker):
    id = "Checker.MagicDRC"
    flow_control_variable = "QUIT_ON_MAGIC_DRC"
    name = "Magic DRC Checker"
    long_name = "Magic Design Rule Checker"

    metric_name = "magic__drc_error__count"
    metric_description = "Magic DRC errors"

    config_vars = [
        Variable(
            "QUIT_ON_MAGIC_DRC",
            bool,
            "Checks for DRC violations after magic DRC is executed and exits the flow if any was found.",
            default=True,
        ),
    ]


@Step.factory.register()
class IllegalOverlap(MetricChecker):
    id = "Checker.IllegalOverlap"
    flow_control_variable = "QUIT_ON_ILLEGAL_OVERLAPS"
    name = "Illegal Overlap Checker"
    long_name = "Spice Extraction-based Illegal Overlap Checker"

    metric_name = "magic__illegal_overlap__count"
    metric_description = "Magic Illegal Overlap errors"

    config_vars = [
        Variable(
            "QUIT_ON_ILLEGAL_OVERLAPS",
            bool,
            "Checks for illegal overlaps during magic extraction. In some cases, these imply existing undetected shorts in the design. It also exits the flow if any was found.",
            default=True,
        ),
    ]


@Step.factory.register()
class DisconnectedPins(MetricChecker):
    id = "Checker.DisconnectedPins"
    flow_control_variable = "QUIT_ON_DISCONNECTED_PINS"
    name = "Disconnected Pins Checker"
    deferred = False

    metric_name = "design__disconnected_pins__count"
    metric_description = "Disconnected pins count"

    config_vars = [
        Variable(
            "QUIT_ON_DISCONNECTED_PINS",
            bool,
            "Checks for disconnected instance pins.",
            default=True,
        ),
    ]


@Step.factory.register()
class WireLength(MetricChecker):
    id = "Checker.WireLength"
    flow_control_variable = "QUIT_ON_LONG_WIRE"
    name = "Wire Length Threshold Checker"

    metric_name = "route__wirelength__max"
    metric_description = "Threshold-surpassing long wires"

    config_vars = [
        Variable(
            "QUIT_ON_LONG_WIRE",
            bool,
            "Exits the flow if any wire length exceeds the threshold set in the PDK.",
            default=False,
        ),
    ]

    def get_threshold(self) -> Optional[Decimal]:
        threshold = self.config["WIRE_LENGTH_THRESHOLD"]
        assert threshold is None or isinstance(threshold, Decimal)
        return threshold

    def get_threshold_description(self) -> Optional[str]:
        return "the threshold specified in the configuration file."


@Step.factory.register()
class XOR(MetricChecker):
    id = "Checker.XOR"
    flow_control_variable = "QUIT_ON_XOR_ERROR"
    name = "XOR Difference Checker"
    long_name = "Magic vs. KLayout XOR Difference Checker"

    metric_name = "design__xor_difference__count"
    metric_description = "XOR differences"

    config_vars = [
        Variable(
            "QUIT_ON_XOR_ERROR",
            bool,
            "Checks for geometric differences between the Magic and KLayout stream-outs.",
            default=True,
        ),
    ]


@Step.factory.register()
class LVS(MetricChecker):
    id = "Checker.LVS"
    flow_control_variable = "QUIT_ON_LVS_ERROR"
    name = "LVS Error Checker"
    long_name = "Layout vs. Schematic Error Checker"

    metric_name = "design__lvs_errors__count"
    metric_description = "LVS errors"

    config_vars = [
        Variable(
            "QUIT_ON_LVS_ERROR",
            bool,
            "Checks for LVS errors after netgen LVS is executed and exits the flow if any was found.",
            default=True,
        ),
    ]

@Step.factory.register()
class LintErrors(MetricChecker):
    id = "Checker.LintErrors"
    flow_control_variable = "QUIT_ON_LINTER_ERRORS"
    name = "Lint Errors Checker"
    long_name = "Lint Errors Checker"

    metric_name = "design__lint_errors"
    metric_description = "Lint errors"

    config_vars = [
        Variable(
            "QUIT_ON_LINTER_ERRORS",
            bool,
            "Quit on linter errors.",
            default=True,
            deprecated_names=["QUIT_ON_VERILATOR_ERRORS"],
        ),
    ]


@Step.factory.register()
class LintWarnings(MetricChecker):
    id = "Checker.LintWarnings"
    flow_control_variable = "QUIT_ON_LINTER_WARNINGS"
    name = "Lint Warnings Checker"
    long_name = "Lint Warnings Checker"

    metric_name = "design__lint_warnings"
    metric_description = "Lint warnings"

    config_vars = [
        Variable(
            "QUIT_ON_LINTER_WARNINGS",
            bool,
            "Quit on linter warnings.",
            default=False,
            deprecated_names=["QUIT_ON_LINTER_ERRORS"],
        ),
    ]

