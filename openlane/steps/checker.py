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

from rich.console import Console
from rich.table import Table

from .step import ViewsUpdate, MetricsUpdate, Step, StepError, DeferredStepError, State

from ..logging import err, warn, info, success


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
                    success(f"Check for {self.metric_description} clear.")
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

    metric_name = "design__disconnected_pins__count"
    metric_description = "Disconnected pins count"


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

    metric_name = "design__lvs_errors__count"
    metric_description = "LVS errors"


@Step.factory.register()
class LintErrors(MetricChecker):
    id = "Checker.LintErrors"
    name = "Lint Errors Checker"
    long_name = "Lint Errors Checker"
    deferred = False

    metric_name = "design__lint_errors__count"
    metric_description = "Lint errors"


@Step.factory.register()
class LintWarnings(MetricChecker):
    id = "Checker.LintWarnings"
    name = "Lint Warnings Checker"
    long_name = "Lint Warnings Checker"
    deferred = False

    metric_name = "design__lint_warnings__count"
    metric_description = "Lint warnings"


@Step.factory.register()
class LintTimingConstructs(MetricChecker):
    id = "Checker.LintTimingConstructs"
    name = "Lint Timing Error Checker"
    long_name = "Lint Timing Errors Checker"
    deferred = False

    metric_name = "design__lint_timing_constructs__count"
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
class QoR(Step):
    id = "Checker.QoR"
    name = "QoR"
    long_name = "QoR"
    inputs = []
    outputs = []

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:

        x = {
            "metrics": {
                "design__lint_errors__count": 0,
                "design__lint_timing_constructs__count": 0,
                "design__lint_warnings__count": 1,
                "design__inferred_latch__count": 0,
                "design__instance__count": 451,
                "design__instance_unmapped__count": 0,
                "synthesis__check_error__count": 0,
                "design__max_slew_violation__count__corner:nom_tt_025C_1v80": 0,
                "design__max_fanout_violation__count__corner:nom_tt_025C_1v80": 0,
                "design__max_cap_violation__count__corner:nom_tt_025C_1v80": 0,
                "power__internal__total": 0.0007471751305274665,
                "power__switching__total": 0.00035998804378323257,
                "power__leakage__total": 4.9222390607894795e-09,
                "power__total": 0.0011071680346503854,
                "clock__skew__worst_hold__corner:nom_tt_025C_1v80": 0.010099,
                "clock__skew__worst_setup__corner:nom_tt_025C_1v80": 0.010099,
                "timing__hold__ws__corner:nom_tt_025C_1v80": 0.330183,
                "timing__setup__ws__corner:nom_tt_025C_1v80": 6.80628,
                "timing__hold__tns__corner:nom_tt_025C_1v80": 0,
                "timing__setup__tns__corner:nom_tt_025C_1v80": 0,
                "timing__hold__wns__corner:nom_tt_025C_1v80": 0,
                "timing__setup__wns__corner:nom_tt_025C_1v80": 0,
                "timing__hold_vio__count__corner:nom_tt_025C_1v80": 0,
                "timing__hold_r2r_vio__count__corner:nom_tt_025C_1v80": 0,
                "timing__setup_vio__count__corner:nom_tt_025C_1v80": 0,
                "timing__setup_r2r_vio__count__corner:nom_tt_025C_1v80": 0,
                "design__max_slew_violation__count": 0,
                "design__max_fanout_violation__count": 0,
                "design__max_cap_violation__count": 0,
                "clock__skew__worst_hold": 0.016675,
                "clock__skew__worst_setup": 0.016675,
                "timing__hold__ws": 0.111121,
                "timing__setup__ws": 5.973317,
                "timing__hold__tns": 0,
                "timing__setup__tns": 0,
                "timing__hold__wns": 0,
                "timing__setup__wns": 0,
                "timing__hold_vio__count": 0,
                "timing__hold_r2r_vio__count": 0,
                "timing__setup_vio__count": 0,
                "timing__setup_r2r_vio__count": 0,
                "design__die__bbox": "0.0 0.0 101.205 111.925",
                "design__core__bbox": "5.52 10.88 95.68 100.64",
                "design__io": 38,
                "design__die__area": 11327.4,
                "design__core__area": 8092.76,
                "design__instance__area": 3595.95,
                "design__instance__count__stdcell": 451,
                "design__instance__area__stdcell": 3595.95,
                "design__instance__count__macros": 0,
                "design__instance__area__macros": 0,
                "design__instance__utilization": 0.444341,
                "design__instance__utilization__stdcell": 0.444341,
                "timing__drv__floating__nets": "0",
                "timing__drv__floating__pins": "0",
                "design__instance__displacement__total": 0,
                "design__instance__displacement__mean": 0,
                "design__instance__displacement__max": 0,
                "route__wirelength__estimated": 5862.04,
                "design__violations": 0,
                "design__instance__count__setup_buffer": 0,
                "design__instance__count__hold_buffer": 0,
                "antenna__violating__nets": 0,
                "antenna__violating__pins": 0,
                "antenna__count": 0,
                "route__net": 384,
                "route__net__special": 2,
                "route__drc_errors__iter:1": 74,
                "route__wirelength__iter:1": 6379,
                "route__drc_errors__iter:2": 13,
                "route__wirelength__iter:2": 6345,
                "route__drc_errors__iter:3": 4,
                "route__wirelength__iter:3": 6356,
                "route__drc_errors__iter:4": 0,
                "route__wirelength__iter:4": 6360,
                "route__drc_errors": 0,
                "route__wirelength": 6360,
                "route__vias": 1979,
                "route__vias__singlecut": 1979,
                "route__vias__multicut": 0,
                "design__disconnected_pins__count": 0,
                "route__wirelength__max": 158.5,
                "design__max_slew_violation__count__corner:nom_ss_100C_1v60": 0,
                "design__max_fanout_violation__count__corner:nom_ss_100C_1v60": 0,
                "design__max_cap_violation__count__corner:nom_ss_100C_1v60": 0,
                "clock__skew__worst_hold__corner:nom_ss_100C_1v60": 0.015353,
                "clock__skew__worst_setup__corner:nom_ss_100C_1v60": 0.015353,
                "timing__hold__ws__corner:nom_ss_100C_1v60": 0.903557,
                "timing__setup__ws__corner:nom_ss_100C_1v60": 5.988363,
                "timing__hold__tns__corner:nom_ss_100C_1v60": 0,
                "timing__setup__tns__corner:nom_ss_100C_1v60": 0,
                "timing__hold__wns__corner:nom_ss_100C_1v60": 0,
                "timing__setup__wns__corner:nom_ss_100C_1v60": 0,
                "timing__hold_vio__count__corner:nom_ss_100C_1v60": 0,
                "timing__hold_r2r_vio__count__corner:nom_ss_100C_1v60": 0,
                "timing__setup_vio__count__corner:nom_ss_100C_1v60": 0,
                "timing__setup_r2r_vio__count__corner:nom_ss_100C_1v60": 0,
                "design__max_slew_violation__count__corner:nom_ff_n40C_1v95": 0,
                "design__max_fanout_violation__count__corner:nom_ff_n40C_1v95": 0,
                "design__max_cap_violation__count__corner:nom_ff_n40C_1v95": 0,
                "clock__skew__worst_hold__corner:nom_ff_n40C_1v95": 0.008493,
                "clock__skew__worst_setup__corner:nom_ff_n40C_1v95": 0.008493,
                "timing__hold__ws__corner:nom_ff_n40C_1v95": 0.112257,
                "timing__setup__ws__corner:nom_ff_n40C_1v95": 7.120349,
                "timing__hold__tns__corner:nom_ff_n40C_1v95": 0,
                "timing__setup__tns__corner:nom_ff_n40C_1v95": 0,
                "timing__hold__wns__corner:nom_ff_n40C_1v95": 0,
                "timing__setup__wns__corner:nom_ff_n40C_1v95": 0,
                "timing__hold_vio__count__corner:nom_ff_n40C_1v95": 0,
                "timing__hold_r2r_vio__count__corner:nom_ff_n40C_1v95": 0,
                "timing__setup_vio__count__corner:nom_ff_n40C_1v95": 0,
                "timing__setup_r2r_vio__count__corner:nom_ff_n40C_1v95": 0,
                "design__max_slew_violation__count__corner:min_tt_025C_1v80": 0,
                "design__max_fanout_violation__count__corner:min_tt_025C_1v80": 0,
                "design__max_cap_violation__count__corner:min_tt_025C_1v80": 0,
                "clock__skew__worst_hold__corner:min_tt_025C_1v80": 0.009255,
                "clock__skew__worst_setup__corner:min_tt_025C_1v80": 0.009255,
                "timing__hold__ws__corner:min_tt_025C_1v80": 0.329278,
                "timing__setup__ws__corner:min_tt_025C_1v80": 6.816953,
                "timing__hold__tns__corner:min_tt_025C_1v80": 0,
                "timing__setup__tns__corner:min_tt_025C_1v80": 0,
                "timing__hold__wns__corner:min_tt_025C_1v80": 0,
                "timing__setup__wns__corner:min_tt_025C_1v80": 0,
                "timing__hold_vio__count__corner:min_tt_025C_1v80": 0,
                "timing__hold_r2r_vio__count__corner:min_tt_025C_1v80": 0,
                "timing__setup_vio__count__corner:min_tt_025C_1v80": 0,
                "timing__setup_r2r_vio__count__corner:min_tt_025C_1v80": 0,
                "design__max_slew_violation__count__corner:min_ss_100C_1v60": 0,
                "design__max_fanout_violation__count__corner:min_ss_100C_1v60": 0,
                "design__max_cap_violation__count__corner:min_ss_100C_1v60": 0,
                "clock__skew__worst_hold__corner:min_ss_100C_1v60": 0.014357,
                "clock__skew__worst_setup__corner:min_ss_100C_1v60": 0.014357,
                "timing__hold__ws__corner:min_ss_100C_1v60": 0.903749,
                "timing__setup__ws__corner:min_ss_100C_1v60": 6.005839,
                "timing__hold__tns__corner:min_ss_100C_1v60": 0,
                "timing__setup__tns__corner:min_ss_100C_1v60": 0,
                "timing__hold__wns__corner:min_ss_100C_1v60": 0,
                "timing__setup__wns__corner:min_ss_100C_1v60": 0,
                "timing__hold_vio__count__corner:min_ss_100C_1v60": 0,
                "timing__hold_r2r_vio__count__corner:min_ss_100C_1v60": 0,
                "timing__setup_vio__count__corner:min_ss_100C_1v60": 0,
                "timing__setup_r2r_vio__count__corner:min_ss_100C_1v60": 0,
                "design__max_slew_violation__count__corner:min_ff_n40C_1v95": 0,
                "design__max_fanout_violation__count__corner:min_ff_n40C_1v95": 0,
                "design__max_cap_violation__count__corner:min_ff_n40C_1v95": 0,
                "clock__skew__worst_hold__corner:min_ff_n40C_1v95": 0.007544,
                "clock__skew__worst_setup__corner:min_ff_n40C_1v95": 0.007544,
                "timing__hold__ws__corner:min_ff_n40C_1v95": 0.111121,
                "timing__setup__ws__corner:min_ff_n40C_1v95": 7.1284,
                "timing__hold__tns__corner:min_ff_n40C_1v95": 0,
                "timing__setup__tns__corner:min_ff_n40C_1v95": 0,
                "timing__hold__wns__corner:min_ff_n40C_1v95": 0,
                "timing__setup__wns__corner:min_ff_n40C_1v95": 0,
                "timing__hold_vio__count__corner:min_ff_n40C_1v95": 0,
                "timing__hold_r2r_vio__count__corner:min_ff_n40C_1v95": 0,
                "timing__setup_vio__count__corner:min_ff_n40C_1v95": 0,
                "timing__setup_r2r_vio__count__corner:min_ff_n40C_1v95": 0,
                "design__max_slew_violation__count__corner:max_tt_025C_1v80": 0,
                "design__max_fanout_violation__count__corner:max_tt_025C_1v80": 0,
                "design__max_cap_violation__count__corner:max_tt_025C_1v80": 0,
                "clock__skew__worst_hold__corner:max_tt_025C_1v80": 0.011078,
                "clock__skew__worst_setup__corner:max_tt_025C_1v80": 0.011078,
                "timing__hold__ws__corner:max_tt_025C_1v80": 0.33196,
                "timing__setup__ws__corner:max_tt_025C_1v80": 6.796295,
                "timing__hold__tns__corner:max_tt_025C_1v80": 0,
                "timing__setup__tns__corner:max_tt_025C_1v80": 0,
                "timing__hold__wns__corner:max_tt_025C_1v80": 0,
                "timing__setup__wns__corner:max_tt_025C_1v80": 0,
                "timing__hold_vio__count__corner:max_tt_025C_1v80": 0,
                "timing__hold_r2r_vio__count__corner:max_tt_025C_1v80": 0,
                "timing__setup_vio__count__corner:max_tt_025C_1v80": 0,
                "timing__setup_r2r_vio__count__corner:max_tt_025C_1v80": 0,
                "design__max_slew_violation__count__corner:max_ss_100C_1v60": 0,
                "design__max_fanout_violation__count__corner:max_ss_100C_1v60": 0,
                "design__max_cap_violation__count__corner:max_ss_100C_1v60": 0,
                "clock__skew__worst_hold__corner:max_ss_100C_1v60": 0.016675,
                "clock__skew__worst_setup__corner:max_ss_100C_1v60": 0.016675,
                "timing__hold__ws__corner:max_ss_100C_1v60": 0.906416,
                "timing__setup__ws__corner:max_ss_100C_1v60": 5.973317,
                "timing__hold__tns__corner:max_ss_100C_1v60": 0,
                "timing__setup__tns__corner:max_ss_100C_1v60": 0,
                "timing__hold__wns__corner:max_ss_100C_1v60": 0,
                "timing__setup__wns__corner:max_ss_100C_1v60": 0,
                "timing__hold_vio__count__corner:max_ss_100C_1v60": 0,
                "timing__hold_r2r_vio__count__corner:max_ss_100C_1v60": 0,
                "timing__setup_vio__count__corner:max_ss_100C_1v60": 0,
                "timing__setup_r2r_vio__count__corner:max_ss_100C_1v60": 0,
                "design__max_slew_violation__count__corner:max_ff_n40C_1v95": 0,
                "design__max_fanout_violation__count__corner:max_ff_n40C_1v95": 0,
                "design__max_cap_violation__count__corner:max_ff_n40C_1v95": 0,
                "clock__skew__worst_hold__corner:max_ff_n40C_1v95": 0.009597,
                "clock__skew__worst_setup__corner:max_ff_n40C_1v95": 0.009597,
                "timing__hold__ws__corner:max_ff_n40C_1v95": 0.113495,
                "timing__setup__ws__corner:max_ff_n40C_1v95": 7.11276,
                "timing__hold__tns__corner:max_ff_n40C_1v95": 0,
                "timing__setup__tns__corner:max_ff_n40C_1v95": 0,
                "timing__hold__wns__corner:max_ff_n40C_1v95": 0,
                "timing__setup__wns__corner:max_ff_n40C_1v95": 0,
                "timing__hold_vio__count__corner:max_ff_n40C_1v95": 0,
                "timing__hold_r2r_vio__count__corner:max_ff_n40C_1v95": 0,
                "timing__setup_vio__count__corner:max_ff_n40C_1v95": 0,
                "timing__setup_r2r_vio__count__corner:max_ff_n40C_1v95": 0,
                "design_powergrid__voltage__worst__net:VPWR__corner:nom_tt_025C_1v80": 1.79871,
                "design_powergrid__drop__average__net:VPWR__corner:nom_tt_025C_1v80": 0.000197993,
                "design_powergrid__drop__worst__net:VPWR__corner:nom_tt_025C_1v80": 0.00128695,
                "ir__voltage__worst": 1.8,
                "ir__drop__avg": 0.000198,
                "ir__drop__worst": 0.00129,
                "design__xor_difference__count": 0,
                "magic__drc_error__count": 0,
                "magic__illegal_overlap__count": 0,
                "design__lvs_device_difference__count": 0,
                "design__lvs_net_differences__count": 0,
                "design__lvs_property_fails__count": 0,
                "design__lvs_errors__count": 0,
                "design__lvs_unmatched_devices__count": 0,
                "design__lvs_unmatched_nets__count": 0,
                "design__lvs_unmatched_pins__count": 0,
            }
        }

        white_list = [
            "design__lvs_errors__count",
            "design__xor_difference__count",
            "timing__hold__ws",
            "timing__setup__ws",
        ]
        metric_values = {
            value: str(state_in.metrics.get(value)) for value in white_list
        }
        for key, value in metric_values.items():
            print(f"{key:}:")
            print(f"\t({value})")

        return {}, {}
