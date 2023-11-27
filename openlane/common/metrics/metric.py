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
from decimal import Decimal
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Optional, Tuple, ClassVar, Dict


from ..types import Number, is_number, is_real_number

MetricAggregator = Tuple[Number, Callable[[Iterable[Number]], Number]]

sum_aggregator: MetricAggregator = (0, lambda x: sum(x))
min_aggregator: MetricAggregator = (inf, min)
max_aggregator: MetricAggregator = (-inf, max)


@dataclass
class MetricComparisonResult:
    """
    :param metric_name: The name of the metric that has been compared
    :param gold: The "gold" value being compared against
    :param new: The new value being evaluated
    :param delta: Non-``None`` if and only if ``before`` - ``after`` is a valid number.
        Evaluates to ``after - before``\\.
    :param delta_pct: Non-``None`` if ``delta`` is not None and before is non-zero.
        Evaluates to ``(after - before) / before * 100``\\.
    :param better: Whether the change in the value is considered a good thing or
        not. ``None`` if ``delta`` is None or has no value set for
        ``Metric.higher_is_better``\\.
    :param critical: Whether this change of value very likely results in a dead
        chip, i.e., an increase in DRC values, or an inexplicable change in
        the number of I/O pins.

        If the :class:`Metric` has ``higher_is_better`` set, a change is critical
        only if it's worse.

        Otherwise, any change is considered ``critical``\\.
    """

    metric_name: str
    gold: Any
    new: Any
    delta: Optional[Number]
    delta_pct: Optional[Number]
    better: Optional[bool]
    critical: bool

    def format_values(self) -> Tuple[str, str, str]:
        before_str = str(self.gold)
        if is_number(self.gold):
            before_str = str(round(self.gold, 6))

        after_str = str(self.new)
        if is_number(self.new):
            after_str = str(round(self.new, 6))

        delta_str = "N/A"
        if self.delta is not None:
            delta_str = str(round(self.delta, 6))
            if self.delta_pct is not None:
                delta_pct_str = str(round(self.delta_pct, 2))
                if self.delta_pct > 0:
                    delta_pct_str = f"+{delta_pct_str}"
                delta_str = f"{delta_str} ({delta_pct_str}%)"

        return before_str, after_str, delta_str


@dataclass
class Metric(object):
    """
    An object storing data about a metric as defined in
    <https://github.com/ieee-ceda-datc/datc-rdf-Metrics4ML>.

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
        this metric is considered "good" (such as: better utilization) or "bad"
        (such as: more antenna violations.)
    :param critical: Whether a change in this value indicates a critical
        failure (or radical change) to the design.

        If ``higher_is_better`` is not null, the change is considered critical
        only if the comparison deems the change worse.
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
        """
        :param modifiers: Modifiers of a metric (i.e. the elements postfixed to the metric in the format {key}:{value})
        :returns: The name with the modifiers added
        """
        return "__".join([self.name] + [f"{k}:{v}" for k, v in modifiers.items()])

    def compare(
        self, gold: Any, new: Any, modifiers: Optional[Mapping[str, str]] = None
    ) -> MetricComparisonResult:
        """
        :param gold: The "gold-standard" value for this metric to compare against
        :param new: The new value for this metric being evaluated
        :param modifier: The modifiers that were parsed from the metric name
            (if applicable)- used to set the ``metric_name`` property of
            :class:`MetricComparisonResult`.
        :returns: The result of comparing two values for this metric.
        """
        is_better = None
        is_critical = self.critical and (gold != new)
        delta = None
        delta_pct = None

        if modifiers is None:
            modifiers = {}

        if is_real_number(gold) and is_real_number(new):
            if isinstance(gold, float) or isinstance(new, float):
                gold = Decimal(gold)
                new = Decimal(new)
            delta = new - gold

            if gold == 0:
                if new == 0:
                    delta_pct = Decimal(0)
            else:
                delta_pct = Decimal((delta / gold) * 100)
                if delta_pct == 0:
                    delta_pct = Decimal(0)  # Fix negative zero

            if self.higher_is_better is not None:
                if self.higher_is_better:
                    is_better = delta >= 0
                else:
                    is_better = delta <= 0
                is_critical = self.critical and not is_better
        elif self.higher_is_better is not None:
            if not is_number(gold):
                raise TypeError(
                    f"'{gold}' is not a number for metric {self.name} with non-None 'higher_is_better' field"
                )
            if not is_number(new):
                raise TypeError(
                    f"'{new}' is not a number  for metric {self.name} with non-None 'higher_is_better' field"
                )

        return MetricComparisonResult(
            self.modified_name(modifiers),
            gold,
            new,
            delta,
            delta_pct,
            is_better,
            is_critical,
        )
