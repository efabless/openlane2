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

import fnmatch

from typing import ClassVar, Tuple, List
from decimal import Decimal
from typing import Optional

from .step import ViewsUpdate, MetricsUpdate, Step, StepError, DeferredStepError, State

from ..logging import err, warn, info, debug, verbose
from ..config import Variable


class MetricChecker(Step):
    """
    Raises a (deferred) error if a Decimal metric exceeds a certain threshold.
    """

    inputs = []
    outputs = []

    metric_name: ClassVar[str] = NotImplemented
    metric_description: ClassVar[str] = NotImplemented
    deferred: ClassVar[bool] = True

    @classmethod
    def get_help_md(Self, **kwargs):  # pragma: no cover
        threshold_string = Self.get_threshold_description(None)
        if threshold_string is None:
            threshold_string = str(Self.get_threshold(None))
        dynamic_docstring = "Raises"
        if Self.deferred:
            dynamic_docstring += " a deferred error"
        else:
            dynamic_docstring += " an immediate error"
        dynamic_docstring += f" if {Self.metric_description} (metric: ``{Self.metric_name}``) are >= {threshold_string}."

        return super().get_help_md(docstring_override=dynamic_docstring, **kwargs)

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
    name = "Unmapped Cells Checker"
    deferred = False

    metric_name = "design__instance_unmapped__count"
    metric_description = "Unmapped Yosys instances"


@Step.factory.register()
class YosysSynthChecks(MetricChecker):
    id = "Checker.YosysSynthChecks"
    name = "Yosys Synth Checks"
    deferred = False

    metric_name = "synthesis__check_error__count"
    metric_description = "Yosys check errors"


@Step.factory.register()
class TrDRC(MetricChecker):
    id = "Checker.TrDRC"
    name = "Routing DRC Checker"
    long_name = "Routing Design Rule Checker"

    metric_name = "route__drc_errors"
    metric_description = "Routing DRC errors"


@Step.factory.register()
class MagicDRC(MetricChecker):
    id = "Checker.MagicDRC"
    name = "Magic DRC Checker"
    long_name = "Magic Design Rule Checker"

    metric_name = "magic__drc_error__count"
    metric_description = "Magic DRC errors"


@Step.factory.register()
class IllegalOverlap(MetricChecker):
    id = "Checker.IllegalOverlap"
    name = "Illegal Overlap Checker"
    long_name = "Spice Extraction-based Illegal Overlap Checker"

    metric_name = "magic__illegal_overlap__count"
    metric_description = "Magic Illegal Overlap errors"


@Step.factory.register()
class DisconnectedPins(MetricChecker):
    id = "Checker.DisconnectedPins"
    name = "Disconnected Pins Checker"
    deferred = False

    metric_name = "design__disconnected_pin__count"
    metric_description = "disconnected pins"


@Step.factory.register()
class WireLength(MetricChecker):
    id = "Checker.WireLength"
    name = "Wire Length Threshold Checker"

    metric_name = "route__wirelength__max"
    metric_description = "Threshold-surpassing long wires"

    def get_threshold(self) -> Optional[Decimal]:
        threshold = self.config["WIRE_LENGTH_THRESHOLD"]
        assert threshold is None or isinstance(threshold, Decimal)
        return threshold

    def get_threshold_description(self) -> Optional[str]:
        return "the threshold specified in the configuration file."


@Step.factory.register()
class XOR(MetricChecker):
    id = "Checker.XOR"
    name = "XOR Difference Checker"
    long_name = "Magic vs. KLayout XOR Difference Checker"

    metric_name = "design__xor_difference__count"
    metric_description = "XOR differences"


@Step.factory.register()
class LVS(MetricChecker):
    id = "Checker.LVS"
    name = "LVS Error Checker"
    long_name = "Layout vs. Schematic Error Checker"

    metric_name = "design__lvs_error__count"
    metric_description = "LVS errors"


@Step.factory.register()
class PowerGridViolations(MetricChecker):
    id = "Checker.PowerGridViolations"
    name = "Power Grid Violation Checker"

    metric_name = "design__power_grid_violation__count"
    metric_description = "power grid violations (as reported by OpenROAD PSM- you may ignore these if LVS passes)"


@Step.factory.register()
class LintErrors(MetricChecker):
    id = "Checker.LintErrors"
    name = "Lint Errors Checker"
    long_name = "Lint Errors Checker"
    deferred = False

    metric_name = "design__lint_error__count"
    metric_description = "Lint errors"


@Step.factory.register()
class LintWarnings(MetricChecker):
    id = "Checker.LintWarnings"
    name = "Lint Warnings Checker"
    long_name = "Lint Warnings Checker"
    deferred = False

    metric_name = "design__lint_warning__count"
    metric_description = "Lint warnings"


@Step.factory.register()
class LintTimingConstructs(MetricChecker):
    id = "Checker.LintTimingConstructs"
    name = "Lint Timing Error Checker"
    long_name = "Lint Timing Errors Checker"
    deferred = False

    metric_name = "design__lint_timing_construct__count"
    metric_description = "Lint Timing Errors"

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        metric_value = state_in.metrics.get(self.metric_name)

        if metric_value is not None:
            if metric_value > 0:
                error_msg = "Timing constructs found in the RTL. Please remove them or wrap them around an ifdef. It heavily unrecommended to rely on timing constructs for synthesis."
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
class KLayoutDRC(MetricChecker):
    id = "Checker.KLayoutDRC"
    name = "KLayout DRC Checker"
    long_name = "KLayout Design Rule Checker"

    metric_name = "klayout__drc_error__count"
    metric_description = "KLayout DRC errors"


class TimingViolations(MetricChecker):
    name = "Timing Violations Checker"
    long_name = "Timing Violations Checker"
    violation_type: str = NotImplemented

    config_vars = [
        Variable(
            "TIMING_VIOLATIONS_CORNERS",
            List[str],
            "A list of wildcards matching IPVT corners to use during checking for timing violations.",
            default=["*tt*"],
        ),
    ]

    def check_timing_violations(
        self,
        metric_basename: str,
        state_in: State,
        threshold: Optional[Decimal],
        violation_type: str,
    ):
        if not threshold:
            threshold = Decimal(0)

        metrics = {
            key: value
            for key, value in state_in.metrics.items()
            if metric_basename in key
        }
        debug("metrics ▶")
        debug(metrics)
        if not metrics:
            warn(f"No metrics found for {metric_basename}")
        else:
            metric_corners = set([key.split(":")[1] for key in metrics.keys()])
            unmatched_config_corners = set(
                [
                    config_corner
                    for config_corner in self.config["TIMING_VIOLATIONS_CORNERS"]
                    if not [
                        corner
                        for corner in metric_corners
                        if fnmatch.fnmatch(corner, config_corner)
                    ]
                ]
            )
            matched_corners = set(
                [
                    corner
                    for corner in metric_corners
                    if [
                        config_corner
                        for config_corner in self.config["TIMING_VIOLATIONS_CORNERS"]
                        if fnmatch.fnmatch(corner, config_corner)
                    ]
                ]
            )
            violating_corners = [
                corner
                for corner in matched_corners
                if metrics[f"{metric_basename}:{corner}"] > threshold
            ]

            debug("corners ▶")
            debug(metric_corners)
            debug("unmatched config corners ▶")
            debug(unmatched_config_corners)
            debug("matched corners ▶")
            debug(matched_corners)
            debug("violating corners ▶")
            debug(violating_corners)

            if unmatched_config_corners:
                msg = "The following specified TIMING_VIOLATIONS_CORNERS:\n"
                msg += "\n".join(unmatched_config_corners)
                raise DeferredStepError(msg)
            if violating_corners:
                msg = f"{violation_type} violations found in the following corners:\n"
                msg += "\n".join(violating_corners)
                raise DeferredStepError(msg)
            else:
                verbose(f"No {violation_type} violations found")

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        self.check_timing_violations(
            f"{self.metric_name}__corner",
            state_in,
            self.get_threshold(),
            self.violation_type,
        )

        return {}, {}


@Step.factory.register()
class SetupViolations(TimingViolations):
    id = "Checker.SetupViolations"
    name = "Setup Timing Violations Checker"
    long_name = "Setup Timing Violations Checker"
    violation_type = "setup"

    metric_name = "timing__setup_vio__count"


@Step.factory.register()
class HoldViolations(TimingViolations):
    id = "Checker.HoldViolations"
    name = "Hold Timing Violations Checker"
    long_name = "Hold Timing Violations Checker"
    violation_type = "hold"

    metric_name = "timing__hold_vio__count"
