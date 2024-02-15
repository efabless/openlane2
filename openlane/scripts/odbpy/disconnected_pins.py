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
import sys
from typing import List, Literal, Union

import odb
import utl

from reader import click, click_odb, OdbReader
from reader import rich
from reader import Table


def is_connected(term: Union[odb.dbITerm, odb.dbBTerm]) -> bool:
    if isinstance(term, odb.dbITerm):
        return term.getNet() is not None
    # all bterms have a net, we need to check if it has another
    net = term.getNet()
    iterms = net.getITerms()
    return len(iterms) != 0


def instance_has_disconnect(instance: odb.dbInst) -> bool:
    inputs = 0
    inputs_connected = 0
    outputs = 0
    outputs_connected = 0
    inouts = 0
    inouts_connected = 0
    for iterm in instance.getITerms():
        polarity: Literal["INPUT", "OUTPUT", "INOUT"] = iterm.getIoType()
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

    # Warn if no outputs are used
    if outputs != 0 and outputs_connected == 0:
        print(
            f"[WARNING] No outputs of instance '{instance.getName()}' are connected- add it to IGNORE_DISCONNECTED_MODULES if this is intentional",
            file=sys.stderr,
        )

    # All inputs/inouts need to be driven
    # At least one output needs to be used if the macro has one or more outputs
    return (
        inputs != inputs_connected
        or (outputs != 0 and outputs_connected == 0)
        or inouts != inouts_connected
    )


def block_has_disconnect(block: odb.dbBlock) -> bool:
    inputs = 0
    inputs_connected = 0
    outputs = 0
    outputs_connected = 0
    inouts = 0
    inouts_connected = 0
    for bterm in block.getBTerms():
        polarity: Literal["INPUT", "OUTPUT", "INOUT"] = bterm.getIoType()
        if polarity == "INPUT":
            inputs += 1
            if is_connected(bterm):
                inputs_connected += 1
        elif polarity == "INOUT":
            inouts += 1
            if is_connected(bterm):
                inouts_connected += 1
        else:
            outputs += 1
            if is_connected(bterm):
                outputs_connected += 1

    # All outputs/inouts need to be driven
    # At least one input has to be used if the block has one or more inputs
    return (
        (inputs != 0 and inputs_connected == 0)
        or outputs != outputs_connected
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
        "Macro/Instance",
        "Power Pins",
        "Disconnected",
        "Signal Pins",
        "Disconnected",
        title="",
    )
    disconnected_pins_count = 0

    for instance in [block] + instances:
        if isinstance(instance, odb.dbBlock):
            if not block_has_disconnect(instance):
                continue
            terms = instance.getBTerms()
        else:
            if not instance_has_disconnect(instance):
                continue
            master = instance.getMaster()
            if master.getName() in ignore_module:
                continue
            terms = instance.getITerms()
        signal_pins = [term.getName() for term in terms if not term.isSpecial()]
        power_pins = [term.getName() for term in terms if term.isSpecial()]
        disconnected_power_pins = [
            term.getName()
            for term in terms
            if term.isSpecial() and not is_connected(term)
        ]
        disconnected_signal_pins = [
            term.getName()
            for term in terms
            if not term.isSpecial() and not is_connected(term)
        ]
        table.add_row(
            instance.getName(),
            "\n".join(power_pins),
            "\n".join(disconnected_power_pins),
            "\n".join(signal_pins),
            "\n".join(disconnected_signal_pins),
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
