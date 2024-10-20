# Copyright 2020-2024 Efabless Corporation
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

#  Parts of this file adapted from https://github.com/YosysHQ/yosys/blob/master/techlibs/common/synth.cc
#
#  Copyright (C) 2012  Claire Xenia Wolf <claire@yosyshq.com>
#
#  Permission to use, copy, modify, and/or distribute this software for any
#  purpose with or without fee is hereby granted, provided that the above
#  copyright notice and this permission notice appear in all copies.
#
#  THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
#  WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
#  MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
#  ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
#  WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
#  ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
#  OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import os
import sys
import json
import shutil

import click

from ys_common import ys
from construct_abc_script import ABCScriptCreator


def openlane_proc(d: ys.Design, report_dir: str):
    d.run_pass("proc_clean")  # Clean up unused procedures
    d.run_pass("proc_rmdead")  # Remove dead procedures
    d.run_pass("proc_prune")  # Prune unused parts of procedures
    d.run_pass("proc_init")  # Initialize procedures
    d.run_pass("proc_arst")  # Analyze reset signals in procedures
    d.run_pass("proc_rom")  # Map ROMs within procedures
    d.run_pass("proc_mux")  # Optimize multiplexers within procedures
    d.tee(
        "proc_dlatch", o=os.path.join(report_dir, "latch.rpt")
    )  # Report latches after procedure processing
    d.run_pass("proc_dff")  # Analyze flip-flops within procedures
    d.run_pass("proc_memwr")  # Analyze memory writes within procedures
    d.run_pass("proc_clean")  # Clean up after procedure processing
    d.tee("check", o=os.path.join(report_dir, "pre_synth_chk.rpt"))
    d.run_pass("opt_expr")  # Optimize expressions


def openlane_synth(d, top, flatten, report_dir, *, booth=False, abc_dff=False):
    d.run_pass("hierarchy", "-check", "-top", top, "-nokeep_prints", "-nokeep_asserts")
    openlane_proc(d, report_dir)

    if flatten:
        d.run_pass("flatten")  # Flatten the design hierarchy

    d.run_pass("opt_expr")  # Optimize expressions again

    d.run_pass("opt_clean")  # Clean up after optimization

    # Perform various logic optimization passes
    d.run_pass("opt", "-nodffe", "-nosdff")  # Optimize logic excluding flip-flops
    d.run_pass("fsm")  # Identify and optimize finite state machines
    d.run_pass("opt")  # Additional logic optimization
    d.run_pass("wreduce")  # Reduce logic using algebraic rewriting
    d.run_pass("peepopt")  # Perform local peephole optimization
    d.run_pass("opt_clean")  # Clean up after optimization
    if booth:
        d.run_pass("booth")
    d.run_pass("alumacc")  # Optimize arithmetic logic unitsb
    d.run_pass("share")  # Share logic across the design
    d.run_pass("opt")  # More logic optimization

    # Memory optimization
    d.run_pass("memory", "-nomap")  # Analyze memories but don't map them yet
    d.run_pass("opt_clean")  # Clean up after memory analysis

    # Perform more aggressive optimization with faster runtime
    d.run_pass("opt", "-fast", "-full")  # Fast and comprehensive optimization

    # Technology mapping
    d.run_pass("memory_map")  # Map memories to standard cells
    d.run_pass("opt", "-full")  # More optimization after memory mapping
    d.run_pass("techmap")  # Map logic to standard cells from the technology library
    d.run_pass("opt", "-fast")  # Fast optimization after technology mapping
    d.run_pass("opt", "-fast")  # More fast optimization

    d.run_pass(
        "abc", "-fast", *(["-dff"] if abc_dff else [])
    )  # Run ABC with fast settings
    d.run_pass("opt", "-fast")  # MORE fast optimization

    # Checks and Stats
    d.run_pass("hierarchy", "-check", "-top", top, "-nokeep_prints", "-nokeep_asserts")
    d.run_pass("check")
    d.run_pass("stat")


@click.command()
@click.option("--output", type=click.Path(exists=False, dir_okay=False), required=True)
@click.option("--config-in", type=click.Path(exists=True), required=True)
@click.option("--extra-in", type=click.Path(exists=True), required=True)
@click.option("--lighter-dff-map", type=click.Path(exists=True), required=False)
def synthesize(
    output,
    config_in,
    extra_in,
    lighter_dff_map,
):
    config = json.load(open(config_in))
    extra = json.load(open(extra_in))

    includes = config.get("VERILOG_INCLUDE_DIRS") or []
    defines = (config.get("VERILOG_DEFINES") or []) + [
        f"PDK_{config['PDK']}",
        f"SCL_{config['STD_CELL_LIBRARY']}",
        "__openlane__",
        "__pnr__",
    ]

    blackbox_models = extra["blackbox_models"]
    libs = extra["libs_synth"]

    d = ys.Design()

    step_dir = os.path.dirname(output)
    report_dir = os.path.join(step_dir, "reports")
    os.makedirs(report_dir, exist_ok=True)

    d.add_blackbox_models(blackbox_models, includes=includes, defines=defines)

    clock_period = config["CLOCK_PERIOD"] * 1000  # ns -> ps

    # ABC only supports these two:
    # https://github.com/YosysHQ/abc/blob/28d955ca97a1c4be3aed4062aec0241a734fac5d/src/map/scl/sclUtil.c#L257
    sdc_path = os.path.join(step_dir, "synthesis.abc.sdc")
    with open(sdc_path, "w") as f:
        print(f"set_driving_cell {config['SYNTH_DRIVING_CELL']}", file=f)
        print(f"set_load {config['OUTPUT_CAP_LOAD']}", file=f)

    ys.log(f"[INFO] Using SDC file '{sdc_path}' for ABC…")

    if verilog_files := config.get("VERILOG_FILES"):
        d.read_verilog_files(
            verilog_files,
            top=config["DESIGN_NAME"],
            synth_parameters=config["SYNTH_PARAMETERS"] or [],
            includes=includes,
            defines=defines,
            use_synlig=config["USE_SYNLIG"],
            synlig_defer=config["SYNLIG_DEFER"],
        )
    elif vhdl_files := config.get("VHDL_FILES"):
        d.run_pass("plugin", "-i", "ghdl")
        d.run_pass("ghdl", *vhdl_files, "-e", config["DESIGN_NAME"])
    else:
        print(
            "Script called inappropriately: config must include either VERILOG_FILES or VHDL_FILES.",
            file=sys.stderr,
        )
        exit(1)

    d.run_pass(
        "hierarchy",
        "-check",
        "-top",
        config["DESIGN_NAME"],
        "-nokeep_prints",
        "-nokeep_asserts",
    )
    d.run_pass("rename", "-top", config["DESIGN_NAME"])
    d.run_pass("select", "-module", config["DESIGN_NAME"])
    try:
        d.run_pass(
            "show", "-format", "dot", "-prefix", os.path.join(step_dir, "hierarchy")
        )
    except Exception:
        pass
    d.run_pass("select", "-clear")

    lib_arguments = []
    for lib in libs:
        lib_arguments.extend(["-liberty", lib])

    if config["SYNTH_ELABORATE_ONLY"]:
        openlane_proc(d, report_dir)
        if config["SYNTH_ELABORATE_FLATTEN"]:
            d.run_pass("flatten")
        d.run_pass("setattr", "-set", "keep", "1")
        d.run_pass("splitnets")
        d.run_pass("opt_clean", "-purge")
        d.tee("check", o=os.path.join(report_dir, "chk.rpt"))
        d.tee("stat", "-json", *lib_arguments, o=os.path.join(report_dir, "stat.json"))
        d.tee("stat", *lib_arguments, o=os.path.join(report_dir, "stat.rpt"))

        d.run_pass(
            "write_verilog",
            "-noattr",
            "-noexpr",
            "-nohex",
            "-nodec",
            "-defparam",
            output,
        )
        d.run_pass("write_json", f"{output}.json")
        exit(0)

    if config["SYNTH_TRISTATE_MAP"] is not None:
        d.run_pass("tribuf")

    adder_type = config["SYNTH_ADDER_TYPE"]
    if adder_type not in ["YOSYS", "FA"]:
        if mapping := config[f"SYNTH_{adder_type}_MAP"]:
            ys.log(f"[INFO] Applying {adder_type} mapping from '{mapping}'…")
            d.run_pass("techmap", "-map", mapping)

    if mapping := lighter_dff_map:
        ys.log(f"[INFO] Using Lighter with mapping '{mapping}'…")
        d.run_pass("plugin", "-i", "lighter")
        d.run_pass("reg_clock_gating", "-map", mapping)

    openlane_synth(
        d,
        config["DESIGN_NAME"],
        not config["SYNTH_NO_FLAT"],
        report_dir,
        booth=config["SYNTH_MUL_BOOTH"],
        abc_dff=config["SYNTH_ABC_DFF"],
    )

    d.run_pass("delete", "t:$print")
    d.run_pass("delete", "t:$assert")

    try:
        d.run_pass(
            "show",
            "-format",
            "dot",
            "-prefix",
            os.path.join(step_dir, "primitive_techmap"),
        )
    except Exception:
        pass

    d.run_pass("opt")
    d.run_pass("opt_clean", "-purge")

    d.tee(
        "stat", "-json", *lib_arguments, o=os.path.join(report_dir, "pre_techmap.json")
    )
    d.tee("stat", *lib_arguments, o=os.path.join(report_dir, "pre_techmap.rpt"))

    if tristate_mapping := config["SYNTH_TRISTATE_MAP"]:
        ys.log(f"[INFO] Applying tri-state buffer mapping from '{tristate_mapping}'…")
        d.run_pass("techmap", "-map", tristate_mapping)
        d.run_pass("simplemap")
    if fa_mapping := config["SYNTH_FA_MAP"]:
        if adder_type == "FA":
            ys.log(f"[INFO] Applying full-adder mapping from '{fa_mapping}'…")
            d.run_pass("techmap", "-map", fa_mapping)
    if latch_mapping := config["SYNTH_LATCH_MAP"]:
        ys.log(f"[INFO] Applying latch mapping from '{latch_mapping}'…")
        d.run_pass("techmap", "-map", latch_mapping)
        d.run_pass("simplemap")
    if extra_mapping := config["SYNTH_EXTRA_MAPPING_FILE"]:
        ys.log(f"[INFO] Applying extra mappings from '{extra_mapping}'…")
        d.run_pass("techmap", "-map", extra_mapping)

    dfflibmap_args = []
    for lib in libs:
        dfflibmap_args.extend(["-liberty", lib])
    d.run_pass("dfflibmap", *dfflibmap_args)

    d.tee("stat", "-json", *lib_arguments, o=os.path.join(report_dir, "post_dff.json"))
    d.tee("stat", *lib_arguments, o=os.path.join(report_dir, "post_dff.rpt"))

    script_creator = ABCScriptCreator(config)

    def run_strategy(d):
        abc_script = script_creator.generate_abc_script(
            step_dir,
            config["SYNTH_STRATEGY"],
        )
        ys.log(f"[INFO] Using generated ABC script '{abc_script}'…")
        d.run_pass(
            "abc",
            "-script",
            abc_script,
            "-D",
            f"{clock_period}",
            "-constr",
            sdc_path,
            "-showtmp",
            *lib_arguments,
            *(["-dff"] if config["SYNTH_ABC_DFF"] else []),
        )

        d.run_pass("setundef", "-zero")
        d.run_pass(
            "hilomap",
            "-hicell",
            *config["SYNTH_TIEHI_CELL"].split("/"),
            "-locell",
            *config["SYNTH_TIELO_CELL"].split("/"),
        )

        if config["SYNTH_SPLITNETS"]:
            d.run_pass("splitnets")
            d.run_pass("opt_clean", "-purge")

        if config["SYNTH_DIRECT_WIRE_BUFFERING"]:
            d.run_pass("insbuf", "-buf", *config["SYNTH_BUFFER_CELL"].split("/"))

        d.tee("check", o=os.path.join(report_dir, "chk.rpt"))
        d.tee("stat", "-json", *lib_arguments, o=os.path.join(report_dir, "stat.json"))
        d.tee("stat", *lib_arguments, o=os.path.join(report_dir, "stat.rpt"))

        if config["SYNTH_AUTONAME"]:
            # Generate public names for the various nets, resulting in very long
            # names that include the full hierarchy, which is preferable to the
            # internal names that are simply sequential numbers such as `_000019_`.
            # Renamed net names can be very long, such as:
            #     manual_reset_gf180mcu_fd_sc_mcu7t5v0__dffq_1_Q_D_gf180mcu_ \
            #     fd_sc_mcu7t5v0__nor3_1_ZN_A1_gf180mcu_fd_sc_mcu7t5v0__aoi21_ \
            #     1_A2_A1_gf180mcu_fd_sc_mcu7t5v0__nand3_1_ZN_A3_gf180mcu_fd_ \
            #     sc_mcu7t5v0__and3_1_A3_Z_gf180mcu_fd_sc_mcu7t5v0__buf_1_I_Z
            d.run_pass("autoname")

        d.run_pass(
            "write_verilog",
            "-noattr",
            "-noexpr",
            "-nohex",
            "-nodec",
            "-defparam",
            output,
        )
        d.run_pass("write_json", f"{output}.json")

    run_strategy(d)

    if config["SYNTH_NO_FLAT"]:
        # Resynthesize, flattening
        d_flat = ys.Design()
        d_flat.add_blackbox_models(blackbox_models)

        shutil.copy(output, f"{output}.hierarchy.nl.v")
        d_flat.run_pass("read_verilog", "-sv", output)
        d_flat.run_pass(
            "synth",
            "-flatten",
            *(["-booth"] if config["SYNTH_MUL_BOOTH"] else []),
        )
        run_strategy(d_flat)


if __name__ == "__main__":
    synthesize()
