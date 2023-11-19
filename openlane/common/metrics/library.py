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
from math import inf
from typing import Callable, Iterable, Optional, Tuple, ClassVar, Dict


from ..types import Number

AggregationInfo = Tuple[Number, Callable[[Iterable[Number]], Number]]

sum_aggregator: AggregationInfo = (0, lambda x: sum(x))
min_aggregator: AggregationInfo = (inf, min)
max_aggregator: AggregationInfo = (-inf, max)


class Metric(object):
    """
    An object storing data about a metric.

    :param name: The string name of the metric.
    :param aggregator: A tuple of:
        - A starting value for an accumulator
        - A reduction function

        The aim is the ability to aggregate values from various sub-metrics,
        i.e., for the metric ``timing__hold_vio__count``, the sub-metrics:

        - ``timing__hold_vio__count__corner:A``
        - ``timing__hold_vio__count__corner:B``

        Would be summed up to generate the value for ``timing__hold_vio__count``.
    :param higher_is_better: At a high level, whether a higher numeric value for
        this metric is considered "good" (such as, better utilization) or "bad"
        (such as: more antenna violations.)
    """

    name: str
    aggregator: Optional[AggregationInfo] = None
    higher_is_better: Optional[bool] = None
    dont_aggregate: Optional[Iterable[str]] = None

    by_name: ClassVar[Dict[str, "Metric"]] = {}

    def __init__(
        self,
        name: str,
        *,
        aggregator: Optional[AggregationInfo] = None,
        higher_is_better: Optional[bool] = None,
        dont_aggregate: Optional[Iterable[str]] = None,
    ) -> None:
        self.name = name
        self.aggregator = aggregator
        self.higher_is_better = higher_is_better
        self.dont_aggregate = dont_aggregate

        Metric.by_name[name] = self


Metric(
    "timing__hold_vio__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "timing__hold_r2r_vio__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "timing__setup_vio__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "timing__setup_r2r_vio__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__max_slew_violation__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__max_fanout_violation__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__max_cap_violation__count",
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
    "design__core__area",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__die__area",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__instance__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__instance_unmapped__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__instance__area",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__lint_timing_constructs__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__lint_warnings__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__lint_errors__count",
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
)


Metric(
    "route__drc_errors",
    aggregator=sum_aggregator,
    higher_is_better=False,
    dont_aggregate=["iter"],
)
Metric(
    "magic__drc_error__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "magic__illegal_overlap__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "route__antenna_violations__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
    dont_aggregate=["iter"],
)
Metric(
    "design__disconnected_pins__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__inferred_latch__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "synthesis__check_error__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)


Metric(
    "design__lvs_device_difference__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__lvs_errors__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__lvs_net_differences__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__lvs_property_fails__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__lvs_unmatched_devices__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__lvs_unmatched_nets__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)
Metric(
    "design__lvs_unmatched_pins__count",
    aggregator=sum_aggregator,
    higher_is_better=False,
)

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
    "clock__skew__worst_hold",
    aggregator=max_aggregator,
    higher_is_better=False,
)
Metric(
    "clock__skew__worst_setup",
    aggregator=max_aggregator,
    higher_is_better=False,
)
Metric(
    "route__wirelength__max",
    aggregator=max_aggregator,
    higher_is_better=False,
    dont_aggregate=["iter"],
)
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
Metric(
    "timing__hold__ws",
    aggregator=min_aggregator,
    higher_is_better=True,
)
Metric(
    "timing__setup__ws",
    aggregator=min_aggregator,
    higher_is_better=True,
)
Metric(
    "timing__hold__wns",
    aggregator=min_aggregator,
    higher_is_better=True,
)
Metric(
    "timing__setup__wns",
    aggregator=min_aggregator,
    higher_is_better=True,
)
Metric(
    "timing__hold__tns",
    aggregator=sum_aggregator,
    higher_is_better=True,
)
Metric(
    "timing__setup__tns",
    aggregator=sum_aggregator,
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
