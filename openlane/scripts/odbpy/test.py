# Copyright 2022 Efabless Corporation
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
from collections import namedtuple
import json
import re

from reader import click, click_odb, OdbReader
import odb, utl


Module = namedtuple("Module", ["name", "power_pins", "ground_pins"])
Instance = namedtuple(
    "Instance",
    ["name", "module", "power_connections", "ground_connections"],
)


def extract_modules(db, design_json, design_name):
    module_names = [
        design_json["modules"][design_name]["cells"][cell_name]["type"]
        for cell_name in design_json["modules"][design_name]["cells"]
    ]

    modules = []
    for module_name in module_names:
        pins = db.findMaster(module_name).getMTerms()
        power_pins = [pin.getName() for pin in pins if pin.getSigType() == "POWER"]
        ground_pins = [pin.getName() for pin in pins if pin.getSigType() == "GROUND"]
        m = Module(name=module_name, power_pins=power_pins, ground_pins=ground_pins)
        modules.append(m)

    return modules


def is_power(db, module_name, pin_name):
    master = db.findMaster(module_name)
    if master is None:
        return False

    pin = next(
        pin
        for pin in master.getMTerms()
        if pin.getName() == pin_name
    )
    return pin.getSigType() == "POWER"


def is_ground(db, module_name, pin_name):
    master = db.findMaster(module_name)
    if master is None:
        return False

    pin = next(
        pin
        for pin in db.findMaster(module_name).getMTerms()
        if pin.getName() == pin_name
    )
    return pin.getSigType() == "GROUND"


def is_bus(pin_connections):
    return len(pin_connections) > 1


def extract_net_name(design_json, design_name, connection_bit):
    assert len(connection_bit) == 1
    nets = design_json["modules"][design_name]["netnames"]
    net = next(
        wire_name
        for wire_name in nets.keys()
        if nets[wire_name]["bits"] == connection_bit
    )
    return net


def extract_power_pins(db, design_json, design_name, cell_name):
    cells = design_json["modules"][design_name]["cells"]
    module = cells[cell_name]["type"]
    non_bus_pins = {
        pin_name: cells[cell_name]["connections"][pin_name]
        for pin_name in cells[cell_name]["connections"].keys()
        if not is_bus(cells[cell_name]["connections"][pin_name])
    }
    power_pins = {
        pin_name: non_bus_pins[pin_name]
        for pin_name in non_bus_pins.keys()
        if is_power(db, module, pin_name)
    }
    for pin_name in power_pins.keys():
        connection_bit = power_pins[pin_name]
        net = extract_net_name(design_json, design_name, connection_bit)
        power_pins[pin_name] = net

    return power_pins


def extract_ground_pins(db, design_json, design_name, cell_name):
    cells = design_json["modules"][design_name]["cells"]
    module = cells[cell_name]["type"]
    non_bus_pins = {
        pin_name: cells[cell_name]["connections"][pin_name]
        for pin_name in cells[cell_name]["connections"].keys()
        if not is_bus(cells[cell_name]["connections"][pin_name])
    }
    ground_pins = {
        pin_name: non_bus_pins[pin_name]
        for pin_name in non_bus_pins.keys()
        if is_ground(db, module, pin_name)
    }
    for pin_name in ground_pins.keys():
        connection_bit = ground_pins[pin_name]
        net = extract_net_name(design_json, design_name, connection_bit)
        ground_pins[pin_name] = net

    return ground_pins


def extract_instances(db, design_json, design_name):
    instances = []
    cells = design_json["modules"][design_name]["cells"]
    for cell_name in cells.keys():
        module = cells[cell_name]["type"]
        power_pins = extract_power_pins(db, design_json, design_name, cell_name)
        ground_pins = extract_ground_pins(db, design_json, design_name, cell_name)
        instances.append(
            Instance(
                name=cell_name,
                ground_connections=ground_pins,
                power_connections=power_pins,
                module=module,
            )
        )

    return instances


def add_global_connection(
    design,
    *,
    net_name=None,
    inst_pattern=None,
    pin_pattern=None,
    power=False,
    ground=False,
    region=None,
):
    if net_name is None:
        utl.error(
            utl.PDN,
            1501,
            "The net option for the " + "add_global_connection command is required.",
        )

    if inst_pattern is None:
        inst_pattern = ".*"

    if pin_pattern is None:
        utl.error(
            utl.PDN,
            1502,
            "The pin_pattern option for the "
            + "add_global_connection command is required.",
        )

    net = design.getBlock().findNet(net_name)
    if net is None:
        net = odb.dbNet_create(design.getBlock(), net_name)

    if power and ground:
        utl.error(utl.PDN, 1551, "Only power or ground can be specified")
    elif power:
        net.setSpecial()
        net.setSigType("POWER")
    elif ground:
        net.setSpecial()
        net.setSigType("GROUND")

    if region is not None:
        region = design.getBlock().findRegion(region)
        if region is None:
            utl.error(utl.PDN, 1504, f"Region {region} not defined")

    design.getBlock().addGlobalConnect(region, inst_pattern, pin_pattern, net, True)


@click.command()
@click.option("--input-json", required=True)
@click.option("--design-name", required=True)
@click_odb
def cli(input_db, input_json, design_name, reader: OdbReader):

    design_str = open(input_json).read()
    design_json = json.loads(design_str)

    db = reader.db
    chip = db.getChip()

    instances = extract_instances(db, design_json, design_name)
    for instance in instances:
        for pin in instance.power_connections.keys():
            net_name = instance.power_connections[pin]
            add_global_connection(
                design=chip,
                inst_pattern=re.escape(instance.name),
                net_name=net_name,
                pin_pattern=pin,
                power=True,
            )
        for pin in instance.ground_connections.keys():
            net_name = instance.ground_connections[pin]
            add_global_connection(
                design=chip,
                inst_pattern=re.escape(instance.name),
                net_name=net_name,
                pin_pattern=pin,
                ground=True,
            )


if __name__ == "__main__":
    cli()
