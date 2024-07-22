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
import re

from collections import Counter
from reader import click, click_odb, OdbReader, Table, rich


def fill_table(frequency: dict, table: Table):
    sorted_freq = {k: frequency[k] for k in sorted(frequency)}
    for key, value in sorted_freq.items():
        table.add_row(key, str(value))


@click.command()
@click.option(
    "--buffer-list",
    type=click.Path(file_okay=True, dir_okay=False),
    help="List of wildcard strings",
)
@click_odb
def main(
    buffer_list,
    reader: OdbReader,
):
    db = reader.db
    block = db.getChip().getBlock()

    pattern = r"^(\S+)__(\S+)_+\d+"
    compiled_pattern = re.compile(pattern)

    cell_frequency_table = Table(
        "Cell",
        "Count",
        title="Cell Count",
    )
    std_cell_library_table = Table(
        "SCL",
        "Count",
        title="SCL Count",
    )
    cell_type_table = Table(
        "Cell Type", "Count", title="SCL Type Count", title_justify="center"
    )
    buffer_table = Table(
        "Buffer",
        "Count",
        title="Buffer Count",
    )

    cell_frequency = {}
    std_cell_library_freq = {}
    cell_type_frequency = {}
    cells = [instance.getMaster().getName() for instance in block.getInsts()]
    buffers = open(buffer_list).read().split()
    buffer_frequency = Counter([cell for cell in cells if cell in buffers])
    cell_frequency = Counter(cells)

    for cell in cell_frequency.keys():
        result = compiled_pattern.findall(cell)
        if result:
            std_cell_library, cell_type = result[0]
            cell_type_key = f"{std_cell_library}__{cell_type}"
            if std_cell_library_freq.get(std_cell_library) is not None:
                std_cell_library_freq[std_cell_library] += int(cell_frequency[cell])
            else:
                std_cell_library_freq[std_cell_library] = int(cell_frequency[cell])

            if cell_type_frequency.get(cell_type_key) is not None:
                cell_type_frequency[cell_type_key] += int(cell_frequency[cell])
            else:
                cell_type_frequency[cell_type_key] = int(cell_frequency[cell])

    fill_table(
        {k: cell_type_frequency[k] for k in sorted(cell_type_frequency)},
        cell_type_table,
    )
    fill_table({k: buffer_frequency[k] for k in sorted(buffer_frequency)}, buffer_table)
    fill_table(
        {k: cell_frequency[k] for k in sorted(cell_frequency)}, cell_frequency_table
    )
    fill_table(
        {k: std_cell_library_freq[k] for k in sorted(std_cell_library_freq)},
        std_cell_library_table,
    )

    rich.print(cell_frequency_table)
    rich.print(cell_type_table)
    rich.print(std_cell_library_table)
    rich.print(buffer_table)


if __name__ == "__main__":
    main()
