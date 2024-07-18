# Copyright 2022 Efabless Corporation
#
# This file is part of the DFFRAM Memory Compiler.
# See https://github.com/Cloud-V/DFFRAM for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from decimal import Decimal

import utl
import fnmatch

from reader import click, click_odb, OdbReader


def fnmatch_array(name, pattern_array):
    matches = [name for pattern in pattern_array if fnmatch.fnmatch(name, pattern)]
    return matches != []


@click.command()
@click.option("--tap-cell", multiple=True, type=str, help="List of wildcard strings")
@click.option("--decap-cell", multiple=True, type=str, help="List of wildcard strings")
@click.option("--fill-cell", multiple=True, type=str, help="List of wildcard strings")
@click_odb
def main(
    tap_cell,
    decap_cell,
    fill_cell,
    input_db,
    reader: OdbReader,
):
    db = reader.db
    print(tap_cell)
    print(decap_cell)
    print(fill_cell)

    block = db.getChip().getBlock()
    instances = block.getInsts()
    fills = [
        instance.getName()
        for instance in instances
        if fnmatch_array(instance.getMaster().getName(), fill_cell)
    ]
    decaps = [
        instance.getName()
        for instance in instances
        if fnmatch_array(instance.getMaster().getName(), decap_cell)
    ]
    taps = [
        instance.getName()
        for instance in instances
        if fnmatch_array(instance.getMaster().getName(), tap_cell)
    ]
    print(len(fills))
    print(len(decaps))
    print(len(taps))


if __name__ == "__main__":
    main()
