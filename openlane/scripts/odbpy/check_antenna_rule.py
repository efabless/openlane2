#!/usr/bin/env python3
# Copyright 2024 Efabless Corporation
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
from reader import click_odb, click


@click.option(
    "-c", "--cell-name", required=True, multiple=True, help="Names of cells to check"
)
@click.command()
@click_odb
def check_antenna_rules(reader, cell_name):
    cells = [cell for cell in reader.cells]
    for cell in list(filter(lambda cell: cell.getName() in cell_name, cells)):
        name = cell.getName()
        inout_pins = []
        input_pins = []
        output_pins = []
        for mterm in cell.getMTerms():
            if mterm.getSigType() in ["GROUND", "POWER", "ANALOG"]:
                continue
            name = mterm.getName()
            has_diff_area = mterm.hasDiffArea()
            has_gate_area = (
                mterm.getDefaultAntennaModel()
                and mterm.getDefaultAntennaModel().hasGateArea()
                or False
            )
            io_type = mterm.getIoType()
            if io_type == "INOUT" and (not has_diff_area and not has_gate_area):
                inout_pins.append(name)
            elif io_type == "INPUT" and not has_gate_area:
                input_pins.append(name)
            elif io_type == "OUTPUT" and not has_diff_area:
                output_pins.append(name)
        if inout_pins:
            print(
                f"[WARNING] For cell {name}, the following inout pins have no anetnna model information, they might be disconnected:\n",
                "\n".join(inout_pins),
            )
        if input_pins:
            print(
                f"[WARNING] For cell {name}, the following input pins have no antenna gate information, they might not be connected to a gate:\n",
                "\n".join(input_pins),
            )
        if output_pins:
            print(
                f"[WARNING] For cell {name}, the following output pins have no antenna diffusion information, the might not be driven:\n",
                "\n".join(output_pins),
            )


if __name__ == "__main__":
    check_antenna_rules()
