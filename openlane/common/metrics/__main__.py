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


@cloup.command()
@cloup.option("--rich-table/--markdown-table", default=True)
@cloup.argument("metric_files", nargs=2)
def compare(metric_files, rich_table):
    a, b = metric_files
    a = json.load(open(a, encoding="utf8"), parse_float=Decimal)
    b = json.load(open(b, encoding="utf8"), parse_float=Decimal)

    diff = MetricDiff.from_metrics(a, b)
    if rich_table:
        rich.print(diff.render_rich())
    else:
        rich.print(diff.render_md())


@cloup.group()
def cli():
    pass


cli.add_command(compare)


if __name__ == "__main__":
    cli()
