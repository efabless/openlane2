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
import os
import json
from decimal import Decimal
from typing import Set, Tuple

import rich
import cloup
from rich.markdown import Markdown

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
    "*error*",
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
@cloup.argument("metric_files", nargs=2)
def compare(metric_files: Tuple[str, str], filters: Tuple[str, ...]):
    a_path, b_path = metric_files
    a = json.load(open(a_path, encoding="utf8"), parse_float=Decimal)
    b = json.load(open(b_path, encoding="utf8"), parse_float=Decimal)

    final_filters = []
    for filter in filters:
        if filter == "DEFAULT":
            final_filters += default_filter_set
        else:
            final_filters.append(filter)

    diff = MetricDiff.from_metrics(a, b, Filter(final_filters))
    md_str = diff.render_md(sort_by=("corner", ""))
    rich.print(md_str)


cli.add_command(compare)


@cloup.command(hidden=True)
@cloup.option("--include-tables/--no-tables", default=False)
@cloup.option("--render/--plain", default=True)
@cloup.option("-f", "--filter", "filter_wildcards", multiple=True, default=("DEFAULT",))
@cloup.argument("metric_folders", nargs=2)
def compare_multiple(
    filter_wildcards: Tuple[str, ...],
    render: bool,
    include_tables: bool,
    metric_folders: Tuple[str, str],
):
    path_a, path_b = metric_folders

    a: Set[Tuple[str, str, str]] = set()
    b: Set[Tuple[str, str, str]] = set()

    def add_designs(in_dir: str, to_set: Set[Tuple[str, str, str]]):
        for file in os.listdir(in_dir):
            basename = os.path.basename(file)
            pdk, scl, design = basename.split("-", maxsplit=2)
            if ".metrics.json" in design:
                design = design[: -len(".metrics.json")]
            to_set.add((pdk, scl, design))

    add_designs(path_a, a)
    add_designs(path_b, b)

    not_in_a = b - a
    not_in_b = a - b
    common = a.intersection(b)

    difference_report = ""
    for tup in not_in_a:
        pdk, scl, design = tup
        difference_report += f"* Results for a new test, `{'/'.join(tup)}`, detected.\n"
    for tup in not_in_b:
        pdk, scl, design = tup
        difference_report += (
            f"* ‼️ Results for `{'/'.join(tup)}` appear to be missing!\n"
        )

    final_filters = []
    for wildcard in filter_wildcards:
        if wildcard == "DEFAULT":
            final_filters += default_filter_set
        else:
            final_filters.append(wildcard)

    filter = Filter(final_filters)
    critical_change_report = ""
    tables = ""
    total_critical = 0
    if include_tables:
        tables += "## Per-design breakdown\n\n"
    for pdk, scl, design in sorted(common):
        metrics_a = json.load(
            open(
                os.path.join(path_a, f"{pdk}-{scl}-{design}.metrics.json"),
                encoding="utf8",
            ),
            parse_float=Decimal,
        )

        metrics_b = json.load(
            open(
                os.path.join(path_b, f"{pdk}-{scl}-{design}.metrics.json"),
                encoding="utf8",
            ),
            parse_float=Decimal,
        )

        diff = MetricDiff.from_metrics(
            metrics_a,
            metrics_b,
            filter,
        )

        stats = diff.stats()

        total_critical += stats.critical
        if stats.critical > 0:
            critical_change_report += f"  * `{pdk}/{scl}/{design}`: \n"
            for row in diff.differences:
                if not row.critical:
                    continue
                critical_change_report += (
                    f"    * `{row.metric_name}` ({row.before} -> {row.after}) \n"
                )

        if include_tables:
            tables += (
                f"<details><summary><code>{pdk}/{scl}/{design}</code></summary>\n\n"
            )
            tables += diff.render_md(("corner", ""))
            tables += "\n</details>\n\n"

    if total_critical == 0:
        critical_change_report = (
            "* No critical regressions were detected.\n" + critical_change_report
        )
    else:
        critical_change_report = (
            "* **A number of critical regressions were detected:**\n"
            + critical_change_report
        )

    report = "# CI Report\n\n"
    report += difference_report
    report += critical_change_report
    report += tables

    if render:
        rich.print(Markdown(report))
    else:
        rich.print(report)


cli.add_command(compare_multiple)


if __name__ == "__main__":
    cli()
