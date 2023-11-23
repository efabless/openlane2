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
import json
from decimal import Decimal

import rich
import cloup

from .util import MetricDiff
from ..misc import Filter
from ..cli import formatter_settings


default_filter_set = [
    "design__*__area",
    "design__max_*",
    "design__lvs_error__count",
    "antenna__violating*",
    "clock__*",
    "ir__*",
    "power__*",
    "timing__*_vio__*",
    "*errors*",
    "!*__iter:*",
]


@cloup.group(
    no_args_is_help=True,
    formatter_settings=formatter_settings,
)
def cli():
    pass


@cloup.command()
@cloup.option("-f", "--filter", "filters", multiple=True, default=("DEFAULT",))
@cloup.option("--rich-table/--markdown-table", default=True)
@cloup.argument("metric_files", nargs=2)
def compare(metric_files, rich_table, filters):
    a, b = metric_files
    a = json.load(open(a, encoding="utf8"), parse_float=Decimal)
    b = json.load(open(b, encoding="utf8"), parse_float=Decimal)

    final_filters = []
    for filter in filters:
        if filter == "DEFAULT":
            final_filters += default_filter_set
        else:
            final_filters.append(filter)

    diff = MetricDiff.from_metrics(a, b, Filter(final_filters))
    if rich_table:
        rich.print(diff.render_rich(sort_by=("corner", "")))
    else:
        rich.print(diff.render_md(sort_by=("corner", "")))


cli.add_command(compare)


if __name__ == "__main__":
    cli()
