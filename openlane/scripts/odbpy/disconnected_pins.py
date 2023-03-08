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
from typing import List

import click
import rich
import rich.table

from reader import click_odb, OdbReader

import utl


def isConnected(iterm):
    return iterm.getNet() is not None


def isSpecial(iterm):
    return iterm.getSigType() == "POWER" or iterm.getSigType() == "GROUND"


def hasDisconnect(instance):
    return (
        True
        if [iterm for iterm in instance.getITerms() if not isConnected(iterm)]
        else False
    )


@click.option("--ignore-master", default="", type=str, help="Master cells to ignore")
@click.command()
@click_odb
def main(
    reader: OdbReader,
    ignore_master: List[str],
):
    db = reader.db
    block = db.getChip().getBlock()
    instances = block.getInsts()
    table = rich.table.Table(
        "Instance", "Power", "Disconnected", "Signal", "Disconnected", title=""
    )
    disconnected_pins_count = 0

    instances_with_disconnect = [
        instance
        for instance in instances
        if hasDisconnect(instance)
        and (instance.getMaster().getName() not in ignore_master)
    ]

    for instance in instances_with_disconnect:
        iterms = instance.getITerms()
        signal_pins = [
            iterm.getMTerm().getName() for iterm in iterms if not isSpecial(iterm)
        ]
        power_pins = [
            iterm.getMTerm().getName() for iterm in iterms if isSpecial(iterm)
        ]
        disconnected_power_pins = [
            iterm.getMTerm().getName()
            for iterm in iterms
            if isSpecial(iterm) and not isConnected(iterm)
        ]
        disconnected_signal_pins = [
            iterm.getMTerm().getName()
            for iterm in iterms
            if not isSpecial(iterm) and not isConnected(iterm)
        ]
        table.add_row(
            instance.getName(),
            ",".join(power_pins),
            ",".join(disconnected_power_pins),
            ",".join(signal_pins),
            ",".join(disconnected_signal_pins),
        )
        disconnected_pins_count += len(disconnected_signal_pins) + len(disconnected_power_pins)
    rich.print(table)

    utl.metric_integer("design__instance__count__disconnected_pins", disconnected_pins_count)


if __name__ == "__main__":
    main()
