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
import odb
import utl

import re
import json
import functools
from dataclasses import dataclass
from typing import Dict, List, Optional

from reader import OdbReader, click_odb, click


@click.group()
def cli():
    pass


class Design(object):
    @dataclass
    class Instance:
        name: str
        module: str
        power_connections: Dict[str, str]
        ground_connections: Dict[str, str]

    def __init__(self, reader: OdbReader, yosys_dict: dict) -> None:
        self.reader = reader
        self.design_name = reader.block.getName()
        self.yosys_dict = yosys_dict
        self.yosys_design_object = yosys_dict["modules"][self.design_name]

        self.pins_by_module_name: Dict[str, Dict[str, odb.dbMTerm]] = {}
        self.verilog_net_name_by_bit: Dict[int, str] = functools.reduce(
            lambda a, b: {**a, **{bit: b[0] for bit in b[1]["bits"]}},
            self.yosys_design_object["netnames"].items(),
            {},
        )
        self.nets_by_net_name = {net.getName(): net for net in reader.block.getNets()}

    def get_pins(self, module_name: str) -> Dict[str, odb.dbMTerm]:
        if module_name not in self.pins_by_module_name:
            master = self.reader.db.findMaster(module_name)
            if master is None:
                print(
                    f"[ERROR] No LEF view for {module_name} was found in the database even though it is declared in the Verilog."
                )
                exit(-1)
            pins = {pin.getName(): pin for pin in master.getMTerms()}
            self.pins_by_module_name[module_name] = pins
        return self.pins_by_module_name[module_name]

    def is_power(self, module_name: str, pin_name: str) -> bool:
        module_pins = self.get_pins(module_name)
        if pin_name not in module_pins:
            print(
                f"[ERROR] No pin {pin_name} found in the module {module_name}'s LEF view: the LEF and Verilog views of the module may be mismatched."
            )
            exit(-1)

        return module_pins[pin_name].getSigType() == "POWER"

    def is_ground(self, module_name: str, pin_name: str) -> bool:
        module_pins = self.get_pins(module_name)
        if pin_name not in module_pins:
            print(
                f"[ERROR] No pin {pin_name} found in the module {module_name}'s LEF view: the LEF and Verilog views of the module may be mismatched."
            )
            exit(-1)

        return module_pins[pin_name].getSigType() == "GROUND"

    def extract_pg_pins(self, cell_name: str) -> dict:
        cells = self.yosys_design_object["cells"]
        module = cells[cell_name]["type"]
        master = self.reader.db.findMaster(module)
        lef_pg_pins = []
        for pin in master.getMTerms():
            if pin.getSigType() in ["POWER", "GROUND"]:
                lef_pg_pins.append((pin.getName(), pin.getSigType()))

        power_pins = {}
        ground_pins = {}
        connections = cells[cell_name]["connections"]
        for pin_name, sigtype in lef_pg_pins:
            if pin_name not in connections:
                # Not connected - continue
                continue
                ## Enforce connections
                print(
                    f"[ERROR] {sigtype} pin {module}/{pin_name} not found in the Verilog view: the LEF and Verilog views of the module may be mismatched."
                )
                print("(Note that power/ground buses are not currently supported.)")
                exit(-1)
            connection_bits = connections[pin_name]
            if len(connection_bits) != 1:
                print(
                    f"[ERROR] Unexpectedly found more than one bit connected to {sigtype} pin {module}/{pin_name}."
                )
                exit(-1)
            connection_bit = connection_bits[0]
            connected_to_v = self.verilog_net_name_by_bit[connection_bit]
            if connected_to_v not in self.nets_by_net_name:
                # Not actually connected - continue
                continue
                ## Enforce connections
                print(
                    f"[ERROR] Could not find net {connected_to_v} connected to {sigtype} pin {module}/{pin_name}."
                )
                print(
                    "(Ensure that the pin(s) in question are properly connected to power or ground.)"
                )
                exit(-1)
            (power_pins if sigtype == "POWER" else ground_pins)[
                pin_name
            ] = connected_to_v

        if len(power_pins) == 0:
            print(
                f"[ERROR] No power pins in {module} appear to be connected to valid nets in the powered netlist."
            )
            exit(-1)
        if len(ground_pins) == 0:
            print(
                f"[ERROR] No ground pins in {module} appear to be connected to valid nets in the powered netlist."
            )
            exit(-1)
        return power_pins, ground_pins

    def extract_instances(self) -> List["Design.Instance"]:
        instances = []
        cells = self.yosys_design_object["cells"]
        for cell_name in cells.keys():
            module = cells[cell_name]["type"]
            if module.startswith("$"):
                # yosys primitive
                continue
            power_pins, ground_pins = self.extract_pg_pins(cell_name)
            instances.append(
                Design.Instance(
                    name=cell_name,
                    ground_connections=ground_pins,
                    power_connections=power_pins,
                    module=module,
                )
            )

        return instances

    def add_global_connection(
        self,
        net_name: str,
        inst_name: str,
        pin_name: str,
        power: bool = False,
        ground: bool = False,
        region: Optional[odb.dbRegion] = None,
    ):
        # Function adapted from OpenROAD
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

        design = self.reader.chip
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

        inst_def_name = self.reader.escape_verilog_name(inst_name)
        pin_def_name = self.reader.escape_verilog_name(pin_name)

        for term in net.getITerms():
            if (
                term.getInst().getName() == inst_def_name
                and term.getMTerm().getName() == pin_def_name
            ):
                print(
                    f"[INFO] {inst_name}/{pin_name} is already connected to {net.getName()} in the layout."
                )
                return

        connected_items = design.getBlock().addGlobalConnect(
            region,
            re.escape(inst_def_name),
            re.escape(pin_def_name),
            net,
            True,
        )

        if connected_items == 0:
            print(
                f"[ERROR] add_global_connections failed to make any connections for '{inst_name}/{pin_name}' to {net_name}."
            )
            exit(-1)
        elif connected_items > 1:
            print(
                f"[ERROR] add_global_connections somehow made {connected_items} connections for '{inst_name}/{pin_name}' to {net_name} -- please report this as a bug"
            )
            exit(-1)
        else:
            print("[INFO] Successfully connected.")


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
    design_str = open(input_json).read()
    yosys_dict = json.loads(design_str)

    design = Design(reader, yosys_dict)
    macro_instances = design.extract_instances()
    for instance in macro_instances:
        for pin in instance.power_connections.keys():
            net_name = instance.power_connections[pin]
            print(f"Connecting power net {net_name} to {instance.name}/{pin}…")
            design.add_global_connection(
                inst_name=instance.name,
                net_name=net_name,
                pin_name=pin,
                power=True,
            )
        for pin in instance.ground_connections.keys():
            net_name = instance.ground_connections[pin]
            print(f"Connecting ground net {net_name} to {instance.name}/{pin}…")
            design.add_global_connection(
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
