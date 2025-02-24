#!/usr/bin/env python3
# Copyright 2020 Efabless Corporation
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
import sys
from reader import click_odb, click, odb
import grt as GRT


@click.command()
@click_odb
def cli(reader):
    grt = reader.design.getGlobalRouter()
    dpl = reader.design.getOpendp()

    insts_to_temporarily_lock_then_unlock_later = []
    for inst in reader.block.getInsts():
        if inst.getPlacementStatus() != "LOCKED":
            insts_to_temporarily_lock_then_unlock_later.append(
                (inst, inst.getPlacementStatus())
            )
            inst.setPlacementStatus("LOCKED")

    reader._grt_setup(grt)

    grt_inc = GRT.IncrementalGRoute(grt, reader.block)
    i = 0

    for target_info in reader.config["INSERT_ECO_BUFFERS"]:
        target_name, target_pin = target_info["target"].split("/")
        name_escaped = reader.escape_verilog_name(target_name)
        buffer_master = target_info["buffer"]

        target = reader.block.findInst(name_escaped)
        if target is None:
            print(f"[ERROR] Instance '{target_name}' not found.", file=sys.stderr)
            exit(-1)

        master = reader.db.findMaster(buffer_master)
        if master is None:
            print(
                f"[ERROR] Buffer type '{buffer_master}' not found.",
                file=sys.stderr,
            )
            exit(-1)

        target_iterm = target.findITerm(target_pin)
        if target_iterm is None:
            print(
                f"[ERROR] Pin '{target_pin}' not found for instance '{target_name}'.",
                file=sys.stderr,
            )
            exit(-1)

        net = target_iterm.getNet()
        if net is None:
            print(
                f"[ERROR] Net not found on pin '{target_pin}' of instance '{target_name}'.",
                file=sys.stderr,
            )
            exit(-1)

        target_iterm.disconnect()

        net_iterms = net.getITerms()
        driver_iterms = [iterm for iterm in net_iterms if iterm.getIoType() == "OUTPUT"]
        if len(driver_iterms) != 1:  # More descriptive error
            print(
                f"[ERROR] Expected 1 driver, found {len(driver_iterms)} for net connected to {target_name}/{target_pin}",
                file=sys.stderr,
            )
            exit(-1)
        driver = driver_iterms[0].getInst()
        if driver is None:  # check if the driver instance exists
            print(
                f"[ERROR] Driver instance not found for net connected to {target_name}/{target_pin}",
                file=sys.stderr,
            )
            exit(-1)

        new_buf_name = f"eco_buffer_{i}"
        new_net_name = f"eco_buffer_{i}_net"
        while (
            reader.block.findInst(new_buf_name) is not None
            or reader.block.findNet(new_net_name) is not None
        ):
            i += 1
            new_buf_name = f"eco_buffer_{i}"
            new_net_name = f"eco_buffer_{i}_net"

        eco_buffer = odb.dbInst.create(reader.block, master, new_buf_name)

        buffer_iterms = eco_buffer.getITerms()
        buffer_a = None
        for iterm in buffer_iterms:
            if iterm.isInputSignal():
                buffer_a = iterm
                break  # Exit loop once input is found
        if buffer_a is None:
            print(
                f"[ERROR] Buffer {buffer_master} has no input signals.", file=sys.stderr
            )
            exit(-1)

        buffer_x = None
        for iterm in buffer_iterms:
            if iterm.isOutputSignal():
                buffer_x = iterm
                break  # Exit loop once output is found
        if buffer_x is None:
            print(
                f"[ERROR] Buffer {buffer_master} has no output signals.",
                file=sys.stderr,
            )
            exit(-1)

        eco_net = odb.dbNet.create(reader.block, new_net_name)

        buffer_a.connect(net)
        buffer_x.connect(eco_net)
        target_iterm.connect(eco_net)

        if target_info.get("placement") is not None:
            eco_x, eco_y = target_info["placement"]
            eco_x = reader.block.micronsToDbu(float(eco_x))
            eco_y = reader.block.micronsToDbu(float(eco_y))
            eco_loc = (eco_x, eco_y)
        else:
            driver_loc = target.getLocation()
            if driver_loc is None:
                print(
                    f"[ERROR] Location not found for driver instance connected to {target_name}/{target_pin}",
                    file=sys.stderr,
                )
                exit(-1)

            dr_x, dr_y = driver_loc
            target_loc = driver.getLocation()
            if target_loc is None:
                print(
                    f"[ERROR] Location not found for target instance {target_name}",
                    file=sys.stderr,
                )
                exit(-1)
            tg_x, tg_y = target_loc
            eco_loc = ((dr_x + tg_x) // 2, (dr_y + tg_y) // 2)

        eco_buffer.setOrient("R0")
        eco_buffer.setLocation(*eco_loc)
        eco_buffer.setPlacementStatus("PLACED")
        grt.addDirtyNet(net)
        grt.addDirtyNet(eco_net)

    site = reader.rows[0].getSite()
    max_disp_x = int(
        reader.design.micronToDBU(reader.config["PL_MAX_DISPLACEMENT_X"])
        / site.getWidth()
    )
    max_disp_y = int(
        reader.design.micronToDBU(reader.config["PL_MAX_DISPLACEMENT_Y"])
        / site.getHeight()
    )
    dpl.detailedPlacement(max_disp_x, max_disp_y)

    grt_inc.updateRoutes(True)

    for inst, previous_status in insts_to_temporarily_lock_then_unlock_later:
        inst.setPlacementStatus(previous_status)


if __name__ == "__main__":
    cli()
