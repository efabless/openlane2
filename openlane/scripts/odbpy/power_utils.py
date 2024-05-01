#!/usr/bin/env python3
# Copyright 2020-2022 Efabless Corporation
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

# Some code adapted from OpenROAD
#
# BSD 3-Clause License
#
# Copyright (c) 2022, The Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
import odb
import utl

import re
import json
from typing import List, Optional
from collections import namedtuple

from reader import OdbReader, click_odb, click


@click.group()
def cli():
    pass


@click.command()
@click.option(
    "--input-json",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    required=True,
)
@click_odb
def set_power_connections(input_json, reader: OdbReader):
    Instance = namedtuple(
        "Instance",
        ["name", "module", "power_connections", "ground_connections"],
    )

    def is_power(db: odb.dbDatabase, module_name: str, pin_name: str) -> bool:
        master = db.findMaster(module_name)
        if master is None:
            return False

        pin = next(pin for pin in master.getMTerms() if pin.getName() == pin_name)
        return pin.getSigType() == "POWER"

    def is_ground(db: odb.dbDatabase, module_name: str, pin_name: str) -> bool:
        master = db.findMaster(module_name)
        if master is None:
            return False

        pin = next(
            pin
            for pin in db.findMaster(module_name).getMTerms()
            if pin.getName() == pin_name
        )
        return pin.getSigType() == "GROUND"

    def is_bus(pin_connections: List) -> bool:
        return len(pin_connections) > 1

    def extract_net_name(
        design_dict: dict, design_name: str, connection_bit: List
    ) -> str:
        assert len(connection_bit) == 1
        nets = design_dict["modules"][design_name]["netnames"]
        net = next(
            wire_name
            for wire_name in nets.keys()
            if nets[wire_name]["bits"] == connection_bit
        )
        return net

    def extract_power_pins(
        db: odb.dbDatabase, design_dict: dict, design_name: str, cell_name: str
    ) -> dict:
        cells = design_dict["modules"][design_name]["cells"]
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
            net = extract_net_name(design_dict, design_name, connection_bit)
            power_pins[pin_name] = net

        return power_pins

    def extract_ground_pins(
        db: odb.dbDatabase, design_dict: dict, design_name: str, cell_name: str
    ) -> dict:
        cells = design_dict["modules"][design_name]["cells"]
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
            net = extract_net_name(design_dict, design_name, connection_bit)
            ground_pins[pin_name] = net

        return ground_pins

    def extract_instances(
        db: odb.dbDatabase,
        design_dict: dict,
        design_name: str,
    ) -> List[Instance]:
        instances = []
        cells = design_dict["modules"][design_name]["cells"]
        for cell_name in cells.keys():
            module = cells[cell_name]["type"]
            power_pins = extract_power_pins(db, design_dict, design_name, cell_name)
            ground_pins = extract_ground_pins(db, design_dict, design_name, cell_name)
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
        net_name: str,
        inst_name: str,
        pin_name: str,
        power: bool = False,
        ground: bool = False,
        region: Optional[odb.dbRegion] = None,
    ):
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
                exit(-1)

        inst_def_name = reader.escape_verilog_name(inst_name)
        pin_def_name = reader.escape_verilog_name(pin_name)

        for term in net.getITerms():
            if (
                term.getInst().getName() == inst_def_name
                and term.getMTerm().getName() == pin_def_name
            ):
                print(f"{inst_name}/{pin_name} is already connected to {net.getName()}")
                return

        connected_items = design.getBlock().addGlobalConnect(
            region,
            re.escape(inst_def_name),
            re.escape(pin_def_name),
            net,
            True,
        )
        print(f"Made {connected_items} connections.")

        assert (
            connected_items != 0
        ), f"Global connect failed to make any connections for '{inst_name}/{pin_name}' to {net_name}"
        assert (
            connected_items == 1
        ), f"Global connect somehow made multiple connections for '{inst_name}/{pin_name}' to {net_name} -- please report this as a bug"

    design_str = open(input_json).read()
    design_dict = json.loads(design_str)

    db = reader.db
    chip = db.getChip()
    design_name = chip.getBlock().getName()

    macro_instances = extract_instances(db, design_dict, design_name)
    for instance in macro_instances:
        for pin in instance.power_connections.keys():
            net_name = instance.power_connections[pin]
            print(f"Connecting power net {net_name} to {instance.name}/{pin}…")
            add_global_connection(
                design=chip,
                inst_name=instance.name,
                net_name=net_name,
                pin_name=pin,
                power=True,
            )
        for pin in instance.ground_connections.keys():
            net_name = instance.ground_connections[pin]
            print(f"Connecting ground net {net_name} to {instance.name}/{pin}…")
            add_global_connection(
                design=chip,
                inst_name=instance.name,
                net_name=net_name,
                pin_name=pin,
                ground=True,
            )


cli.add_command(set_power_connections)


@click.command()
@click.option(
    "--output-vh",
    "output_vh",
    type=click.Path(exists=False, dir_okay=False, writable=True),
    required=True,
)
@click.option(
    "--input-json",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    required=True,
)
@click.option(
    "--power-define",
    type=str,
    required=True,
)
@click_odb
def write_verilog_header(
    output_vh: str,
    input_json: str,
    power_define: str,
    reader: OdbReader,
):
    input_dict = json.load(open(input_json))
    design_name = reader.block.getName()
    pg_bterms = {}
    for bterm in reader.block.getBTerms():
        name, sigtype = bterm.getName(), bterm.getSigType()
        if sigtype in ["POWER", "GROUND"]:
            pg_bterms[name] = sigtype

    design_dict = input_dict["modules"][design_name]
    ports = design_dict["ports"]
    with open(output_vh, "w") as f:
        # For power/ground pins, we rely primarily on the information from the
        # layout as the user may not have defined them in Verilog at all
        pg_decls = []
        for name in pg_bterms:
            direction = "inout"
            if verilog_info := ports.get(name):
                direction = verilog_info["direction"]
            pg_decls.append(f"{direction} {name}")

        # For signals, we rely on the information from the Verilog-generated
        # header as the layout separates buses into individual pins
        signal_decls = []
        for name, info in ports.items():
            if name in pg_bterms:
                continue
            bus_postfix = ""
            # See https://github.com/YosysHQ/yosys/blob/91685355a082f1b5fbc539d0ec484f4d484f5baa/passes/cmds/portlist.cc#L65
            upto = info.get("upto", 0) == 1
            offset = info.get("offset", 0)
            width = len(info["bits"])
            if width > 1:
                msb = offset + width - 1
                lsb = offset
                if upto:
                    msb, lsb = lsb, msb
                bus_postfix = f"[{msb}:{lsb}]"
            signal_decls.append(f"{info['direction']}{bus_postfix} {name}")

        # Write module
        print("// Auto-generated by OpenLane", file=f)
        print(f"module {design_name}(", file=f)
        print(f"`ifdef {power_define}", file=f)
        last_pos = f.tell()
        for decl in pg_decls:
            print(f"  {decl}", file=f, end="")
            last_pos = f.tell()
            print(",", file=f)
        print("`endif", file=f)
        for decl in signal_decls:
            print(f"  {decl}", file=f, end="")
            last_pos = f.tell()
            print(",", file=f)
        f.seek(last_pos)  # Overwrite ,\n
        print("\n);\nendmodule", file=f)


cli.add_command(write_verilog_header)

if __name__ == "__main__":
    cli()
