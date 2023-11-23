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
from math import inf
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Optional, Tuple, ClassVar, Dict


from ..types import Number, is_number

MetricAggregator = Tuple[Number, Callable[[Iterable[Number]], Number]]

sum_aggregator: MetricAggregator = (0, lambda x: sum(x))
min_aggregator: MetricAggregator = (inf, min)
max_aggregator: MetricAggregator = (-inf, max)


@dataclass
class MetricComparisonResult:
    metric_name: str
    before: Any
    after: Any
    delta: Optional[Number]
    delta_pct: Optional[Number]
    better: Optional[bool]
    critical: bool

    def format_values(self) -> Tuple[str, str, str]:
        before_str = str(self.before)
        if is_number(self.before):
            before_str = str(round(self.before, 6))

        after_str = str(self.after)
        if is_number(self.after):
            after_str = str(round(self.after, 6))

        delta_str = "N/A"
        if self.delta is not None:
            delta_str = str(round(self.delta, 6))
            if self.delta_pct is not None:
                delta_pct_str = str(round(self.delta_pct, 2))
                if self.delta_pct >= 0:
                    delta_pct_str = f"+{delta_pct_str}"
                delta_str = f"{delta_str} ({delta_pct_str}%)"

        return before_str, after_str, delta_str


@dataclass
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
    :param critical: Whether a change in this value indicates a critical
        failure (or radical change) to the design.

        If ``higher_is_better`` is not null, the change is considered critical
        only if it is "bad".
    """

    name: str
    aggregator: Optional[MetricAggregator] = None
    higher_is_better: Optional[bool] = None
    dont_aggregate: Optional[Iterable[str]] = None
    critical: bool = False

    by_name: ClassVar[Dict[str, "Metric"]] = {}

    def __post_init__(self):
        Metric.by_name[self.name] = self

    def modified_name(self, modifiers: Mapping[str, str]) -> str:
        return "__".join([self.name] + [f"{k}:{v}" for k, v in modifiers.items()])

    def compare(
        self, lhs: Any, rhs: Any, modifiers: Optional[Mapping[str, str]] = None
    ) -> MetricComparisonResult:
        is_better = None
        is_critical = self.critical and (lhs != rhs)
        delta = None
        delta_pct = None

        if modifiers is None:
            modifiers = {}

        if is_number(lhs) and is_number(rhs):
            delta = rhs - lhs

            if lhs == 0:
                if rhs == 0:
                    delta_pct = Decimal(0)
            else:
                delta_pct = Decimal(((rhs - lhs) / lhs) * 100)

            if self.higher_is_better is not None:
                if self.higher_is_better:
                    is_better = delta >= 0
                else:
                    is_better = delta <= 0
                is_critical = self.critical and not is_better
        elif self.higher_is_better is not None:
            if not is_number(lhs):
                raise TypeError(
                    f"'{lhs}' is not a number for metric {self.name} with non-None 'higher_is_better' field"
                )
            if not is_number(rhs):
                raise TypeError(
                    f"'{rhs}' is not a number  for metric {self.name} with non-None 'higher_is_better' field"
                )

        return MetricComparisonResult(
            self.modified_name(modifiers),
            lhs,
            rhs,
            delta,
            delta_pct,
            is_better,
            is_critical,
        )
