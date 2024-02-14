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

from typing import List, Literal

import odb

from reader import click, click_odb, OdbReader
from reader import rich
from reader import Table

import utl


def is_connected(iterm: odb.dbITerm) -> bool:
    return iterm.getNet() is not None


def is_pg(iterm: odb.dbITerm) -> bool:
    return iterm.getSigType() == "POWER" or iterm.getSigType() == "GROUND"


def get_polarity(iterm: odb.dbITerm) -> Literal["INPUT", "OUTPUT", "INOUT"]:
    return iterm.getIoType()


def has_disconnect(instance: odb.dbInst) -> bool:
    inputs = 0
    inputs_connected = 0
    outputs = 0
    outputs_connected = 0
    inouts = 0
    inouts_connected = 0
    for iterm in instance.getITerms():
        polarity = get_polarity(iterm)
        if polarity == "INPUT":
            inputs += 1
            if is_connected(iterm):
                inputs_connected += 1
        elif polarity == "INOUT":
            inouts += 1
            if is_connected(iterm):
                inouts_connected += 1
        else:
            outputs += 1
            if is_connected(iterm):
                outputs_connected += 1

    return (
        inputs != inputs_connected
        or (outputs != 0 and outputs_connected == 0)
        or inouts != inouts_connected
    )


@click.option(
    "--ignore-module", default=[""], multiple=True, type=str, help="Modules to ignore"
)
@click.command()
@click_odb
def main(
    reader: OdbReader,
    ignore_module: List[str],
):
    db = reader.db
    block = db.getChip().getBlock()
    instances = block.getInsts()
    table = Table(
        "Instance", "Power", "Disconnected", "Signal", "Disconnected", title=""
    )
    disconnected_pins_count = 0

    for instance in instances:
        if not has_disconnect(instance):
            continue
        master = instance.getMaster()
        if master.getName() in ignore_module:
            continue
        iterms = instance.getITerms()
        signal_pins = [
            iterm.getMTerm().getName() for iterm in iterms if not is_pg(iterm)
        ]
        power_pins = [iterm.getMTerm().getName() for iterm in iterms if is_pg(iterm)]
        disconnected_power_pins = [
            iterm.getMTerm().getName()
            for iterm in iterms
            if is_pg(iterm) and not is_connected(iterm)
        ]
        disconnected_signal_pins = [
            iterm.getMTerm().getName()
            for iterm in iterms
            if not is_pg(iterm) and not is_connected(iterm)
        ]
        table.add_row(
            instance.getName(),
            ",".join(power_pins),
            ",".join(disconnected_power_pins),
            ",".join(signal_pins),
            ",".join(disconnected_signal_pins),
        )
        disconnected_pins_count += len(disconnected_signal_pins) + len(
            disconnected_power_pins
        )
    if disconnected_pins_count > 0:
        rich.print(table)

    print(f"Found {disconnected_pins_count} disconnected pin(s).")

    utl.metric_integer("design__disconnected_pin__count", disconnected_pins_count)


if __name__ == "__main__":
    main()
