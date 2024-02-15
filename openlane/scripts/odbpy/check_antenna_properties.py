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
import yaml

from reader import click_odb, click


@click.option(
    "-c", "--cell-name", required=True, multiple=True, help="Names of cells to check"
)
@click.option("-r", "--report-file", help="YAML report file")
@click.command()
@click_odb
def check_antenna_properties(reader, cell_name, report_file):
    cells = [cell for cell in reader.cells]
    report = []

    for cell in list(filter(lambda cell: cell.getName() in cell_name, cells)):
        cell_name = cell.getName()
        inout_pins = []
        input_pins = []
        output_pins = []
        for mterm in cell.getMTerms():
            if mterm.getSigType() in ["GROUND", "POWER", "ANALOG"]:
                continue
            pin_name = mterm.getName()
            has_diff_area = mterm.hasDiffArea()
            has_gate_area = (
                mterm.getDefaultAntennaModel()
                and mterm.getDefaultAntennaModel().hasGateArea()
                or False
            )
            io_type = mterm.getIoType()
            if io_type == "INOUT" and (not has_diff_area and not has_gate_area):
                inout_pins.append(pin_name)
            elif io_type == "INPUT" and not has_gate_area:
                input_pins.append(pin_name)
            elif io_type == "OUTPUT" and not has_diff_area:
                output_pins.append(pin_name)
        if inout_pins:
            print(
                f"[WARNING] Cell '{cell_name}' has ({len(inout_pins)}) inout pin(s) without anetnna gate information not antenna diffusion information. They might be disconnected."
            )
            print("\n".join([f"* {pin}" for pin in inout_pins]))
        if input_pins:
            print(
                f"[WARNING] Cell '{cell_name}' has ({len(input_pins)}) input pin(s) without antenna gate information. They might not be connected to a gate."
            )
        if output_pins:
            print(
                f"[WARNING] Cell '{cell_name}' has ({len(output_pins)}) output pin(s) without antenna diffusion information. They might not be driven."
            )

        entry = {
            "cell": cell_name,
            "inout": inout_pins,
            "output": output_pins,
            "input": input_pins,
        }
        report.append(entry)

    with open(report_file, "w") as f:
        f.write(yaml.dump(report))


if __name__ == "__main__":
    check_antenna_properties()
