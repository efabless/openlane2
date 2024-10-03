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
from .metric import Metric, sum_aggregator, min_aggregator, max_aggregator


# Area and Counts
Metric(
    "design__core__area",
    higher_is_better=False,
)
Metric(
    "design__die__area",
    higher_is_better=False,
)
Metric(
    "design__instance__area",
    higher_is_better=False,
)

# Power
Metric(
    "ir__drop__avg",
    higher_is_better=False,
)
Metric(
    "ir__drop__worst",
    aggregator=max_aggregator,
    higher_is_better=False,
)
Metric(
    "ir__voltage__worst",
    aggregator=min_aggregator,
    higher_is_better=True,
)
Metric(
    "design_powergrid__drop__average",
    higher_is_better=False,
)
Metric(
    "design_powergrid__drop__worst",
    aggregator=max_aggregator,
    higher_is_better=False,
)
Metric(
    "design_powergrid__voltage__worst",
    aggregator=min_aggregator,
    higher_is_better=True,
)
Metric(
    "power__internal__total",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "power__leakage__total",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "power__switching__total",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "power__total",
    aggregator=sum_aggregator,
    higher_is_better=False,
)

# Timing
Metric(
    "timing__hold_vio__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "timing__hold_r2r_vio__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "timing__setup_vio__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)

Metric(
    "timing__setup_r2r_vio__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "timing__hold__ws",
    aggregator=min_aggregator,
    higher_is_better=True,
)
Metric(
    "timing__hold_r2r__ws",
    aggregator=min_aggregator,
    higher_is_better=True,
)
Metric(
    "timing__setup__ws",
    aggregator=min_aggregator,
    higher_is_better=True,
)

Metric(
    "timing__setup_r2r__ws",
    aggregator=min_aggregator,
    higher_is_better=True,
)
Metric(
    "timing__hold__wns",
    aggregator=min_aggregator,
    higher_is_better=True,
    critical=True,
)
Metric(
    "timing__setup__wns",
    aggregator=min_aggregator,
    higher_is_better=True,
    critical=True,
)
Metric(
    "timing__hold__tns",
    aggregator=min_aggregator,
    higher_is_better=True,
    critical=True,
)
Metric(
    "timing__unannotated_net__count",
    aggregator=max_aggregator,
    higher_is_better=False,
)
Metric(
    "timing__unannotated_net_filtered__count",
    aggregator=max_aggregator,
    higher_is_better=False,
)
Metric(
    "timing__setup__tns",
    aggregator=min_aggregator,
    higher_is_better=True,
    critical=True,
)
Metric(
    "clock__skew__worst_hold",
    aggregator=max_aggregator,
    higher_is_better=False,
)
Metric(
    "clock__skew__worst_setup",
    aggregator=min_aggregator,
    higher_is_better=True,
)

# Constraint Violation
Metric(
    "design__max_slew_violation__count",
    aggregator=max_aggregator,
    higher_is_better=False,
)
Metric(
    "design__max_fanout_violation__count",
    aggregator=max_aggregator,
    higher_is_better=False,
)
Metric(
    "design__max_cap_violation__count",
    aggregator=max_aggregator,
    higher_is_better=False,
)

# Placement and Routing
Metric(
    "route__wirelength",
    aggregator=sum_aggregator,
    higher_is_better=False,
    dont_aggregate=["iter"],
)
Metric(
    "route__wirelength__estimated",
    aggregator=sum_aggregator,
    higher_is_better=False,
    dont_aggregate=["iter"],
)
Metric(
    "route__wirelength__max",
    aggregator=max_aggregator,
    higher_is_better=False,
    dont_aggregate=["iter"],
)
Metric(
    "route__antenna_violation__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    dont_aggregate=["iter"],
)
Metric(
    "design__instance__displacement__max",
    aggregator=max_aggregator,
    higher_is_better=False,
)
Metric(
    "design__instance__displacement__total",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__instance__utilization",
    higher_is_better=True,
)

# Potential Issues
Metric(
    "design__lint_warning__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__lint_error__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "design__lint_timing_construct__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "antenna__violating__nets",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "antenna__violating__pins",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__instance_unmapped__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "design__disconnected_pin__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "design__inferred_latch__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__violations",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__xor_difference__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "route__drc_errors",
    aggregator=sum_aggregator,
    higher_is_better=False,
    dont_aggregate=["iter"],
    critical=True,
)
Metric(
    "magic__drc_error__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "magic__illegal_overlap__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "synthesis__check_error__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "design__lvs_error__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "design__lvs_device_difference__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "design__lvs_net_difference__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "design__lvs_property_fail__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "design__lvs_unmatched_device__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "design__lvs_unmatched_net__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
Metric(
    "design__lvs_unmatched_pin__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    critical=True,
)
