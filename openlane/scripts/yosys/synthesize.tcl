# Copyright 2020-2023 Efabless Corporation
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
yosys -import

source $::env(SCRIPTS_DIR)/yosys/common.tcl

set report_dir $::env(STEP_DIR)/reports
file mkdir $report_dir

# Load Macro Dependencies
source $::env(_DEPS_SCRIPT)

# Prepare Liberty Flags
set lib_args [list]
foreach lib $::env(SYNTH_LIBS) {
    lappend lib_args -liberty $lib
}

set dfflib $::env(SYNTH_LIBS)
if {[info exists ::env(DFF_LIB_SYNTH)]} {
    set dfflib $::env(DFF_LIB_SYNTH)
}

set dfflib_args [list]
foreach lib $dfflib {
    lappend dfflib_args -liberty $lib
}

set max_FO $::env(MAX_FANOUT_CONSTRAINT)
set max_TR 0
if { [info exist ::env(MAX_TRANSITION_CONSTRAINT)]} {
    set max_TR [expr {$::env(MAX_TRANSITION_CONSTRAINT) * 1000}]; # ns -> ps
}
set clock_period [expr {$::env(CLOCK_PERIOD) * 1000}]; # ns -> ps

# Create SDC File
set sdc_file $::env(STEP_DIR)/synthesis.sdc
set outfile [open ${sdc_file} w]
puts $outfile "set_driving_cell $::env(SYNTH_DRIVING_CELL)"
puts $outfile "set_load $::env(OUTPUT_CAP_LOAD)"
close $outfile

source $::env(SCRIPTS_DIR)/yosys/construct_abc_script.tcl
set strategy_name $::env(SYNTH_STRATEGY)
set strategy_script [yosys_ol::get_abc_script $strategy_name]

# Start Synthesis
if { [info exists ::env(VERILOG_FILES) ]} {
    yosys_ol::read_verilog_files $::env(DESIGN_NAME)
} elseif { [info exists ::env(VHDL_FILES)] } {
    ghdl {*}$::env(VHDL_FILES) -e $::env(DESIGN_NAME)
} else {
    puts "SCRIPT NOT CALLED CORRECTLY: EITHER VERILOG_FILES OR VHDL_FILES MUST BE SET"
    exit -1
}

hierarchy -check -top $::env(DESIGN_NAME) -nokeep_prints -nokeep_asserts
select -module $::env(DESIGN_NAME)
catch {show -format dot -prefix $::env(STEP_DIR)/hierarchy}
select -clear
yosys rename -top $::env(DESIGN_NAME)

if { $::env(SYNTH_ELABORATE_ONLY) } {
    yosys_ol::ol_proc $report_dir
    if { $::env(SYNTH_ELABORATE_FLATTEN) } {
        flatten
    }

    setattr -set keep 1

    splitnets
    opt_clean -purge

    tee -o "$report_dir/chk.rpt" check
    tee -o "$report_dir/stat.json" stat -json {*}$lib_args
    tee -o "$report_dir/stat.log" stat {*}$lib_args

    write_verilog -noattr -noexpr -nohex -nodec -defparam "$::env(SAVE_NETLIST)"
    write_json "$::env(SAVE_NETLIST).json"
    exit 0
}

# Add various maps
set tbuf_map false
set fa_map false
if { [info exists ::env(SYNTH_TRISTATE_MAP)] } {
    set tbuf_map true
    tribuf
}
set adder_type $::env(SYNTH_ADDER_TYPE)
if { !($adder_type in [list "YOSYS" "FA" "RCA" "CSA"]) } {
    log -stderr "\[ERROR] Misformatted SYNTH_ADDER_TYPE (\"$::env(SYNTH_ADDER_TYPE)\")."
    log -stderr "\[ERROR] Correct format is \"YOSYS|FA|RCA|CSA\"."
    exit 1
}
if { $adder_type == "RCA"} {
    if { [info exists ::env(SYNTH_RCA_MAP)] } {
        log "\[INFO] Applying ripple carry adder mapping from '$::env(RIPPLE_CARRY_ADDER_MAP)'..."
        techmap -map $::env(RIPPLE_CARRY_ADDER_MAP)
    }
} elseif { $adder_type == "CSA"} {
    if { [info exists ::env(SYNTH_CSA_MAP)] } {
        log "\[INFO] Applying carry-select adder mapping from '$::env(SYNTH_CSA_MAP)'..."
        techmap -map $::env(SYNTH_CSA_MAP)
    }
} elseif { $adder_type == "FA"} {
    if { [info exists ::env(SYNTH_FA_MAP)] } {
        set fa_map true
        log "\[INFO] Applying carry-select adder mapping from '$::env(SYNTH_FA_MAP)'..."
    }
}

if { [info exists ::env(_LIGHTER_DFF_MAP)] } {
    puts "Using Lighter with map '$::env(_LIGHTER_DFF_MAP)'…"
    reg_clock_gating -map $::env(_LIGHTER_DFF_MAP)
}

yosys_ol::ol_synth $::env(DESIGN_NAME) $report_dir

delete t:\$print
delete t:\$assert

catch {show -format dot -prefix $::env(STEP_DIR)/primitive_techmap}
opt
opt_clean -purge

tee -o "$report_dir/pre_techmap.json" stat -json {*}$lib_args
tee -o "$report_dir/pre_techmap.log" stat {*}$lib_args

# Techmaps
if { $tbuf_map } {
    log {mapping tbuf}
    log "\[INFO] Applying tri-state buffer mapping from '$::env(SYNTH_TRISTATE_MAP)'..."
    techmap -map $::env(SYNTH_TRISTATE_MAP)
    simplemap
}
if { $fa_map } {
    log "\[INFO] Applying full-adder mapping from '$::env(SYNTH_FA_MAP)'..."
    techmap -map $::env(SYNTH_FA_MAP)
}
if { [info exists ::env(SYNTH_LATCH_MAP)] } {
    log "\[INFO] Applying latch mapping from '$::env(SYNTH_LATCH_MAP)'..."
    techmap -map $::env(SYNTH_LATCH_MAP)
    simplemap
}
if { [info exists ::env(SYNTH_EXTRA_MAPPING_FILE)] } {
    log "\[INFO] Applying extra mappings from '$::env(SYNTH_EXTRA_MAPPING_FILE)'..."
    techmap -map $::env(SYNTH_EXTRA_MAPPING_FILE)
}

dfflibmap {*}$dfflib_args
tee -o "$report_dir/post_dff.json" stat -json {*}$lib_args
tee -o "$report_dir/post_dff.log" stat {*}$lib_args

proc run_strategy {output script strategy_name {postfix_with_strategy 0}} {
    upvar clock_period clock_period
    upvar sdc_file sdc_file
    upvar report_dir report_dir
    upvar lib_args lib_args

    log "\[INFO\] Using strategy \"$strategy_name\"..."

    design -load checkpoint
    abc -D "$clock_period" \
        -constr "$sdc_file" \
        -script "$script" \
        -showtmp \
        {*}$lib_args

    setundef -zero

    hilomap -hicell $::env(SYNTH_TIEHI_CELL) -locell $::env(SYNTH_TIELO_CELL)

    if { $::env(SYNTH_SPLITNETS) } {
        splitnets
        opt_clean -purge
    }

    if { $::env(SYNTH_DIRECT_WIRE_BUFFERING) } {
        insbuf -buf {*}[split $::env(SYNTH_BUFFER_CELL) "/"]
    }

    tee -o "$report_dir/chk.rpt" check
    tee -o "$report_dir/stat.json" stat -json {*}$lib_args
    tee -o "$report_dir/stat.log" stat {*}$lib_args

    if { $::env(SYNTH_AUTONAME) } {
        # Generate public names for the various nets, resulting in very long
        # names that include the full hierarchy, which is preferable to the
        # internal names that are simply sequential numbers such as `_000019_`.
        # Renamed net names can be very long, such as:
        #     manual_reset_gf180mcu_fd_sc_mcu7t5v0__dffq_1_Q_D_gf180mcu_ \
        #     fd_sc_mcu7t5v0__nor3_1_ZN_A1_gf180mcu_fd_sc_mcu7t5v0__aoi21_ \
        #     1_A2_A1_gf180mcu_fd_sc_mcu7t5v0__nand3_1_ZN_A3_gf180mcu_fd_ \
        #     sc_mcu7t5v0__and3_1_A3_Z_gf180mcu_fd_sc_mcu7t5v0__buf_1_I_Z
        autoname
    }
    write_verilog -noattr -noexpr -nohex -nodec -defparam $output
    write_json "$output.json"
    design -reset
}
design -save checkpoint

run_strategy\
    "$::env(SAVE_NETLIST)"\
    "$strategy_script"\
    "$strategy_name"

if { $::env(SYNTH_NO_FLAT) } {
    design -reset

    source $::env(_DEPS_SCRIPT)

    file copy -force $::env(SAVE_NETLIST) $::env(STEP_DIR)/$::env(DESIGN_NAME).hierarchy.nl.v
    read_verilog -sv $::env(SAVE_NETLIST)
    synth -flatten

    design -save checkpoint
    run_strategy\
        "$::env(SAVE_NETLIST)"\
        "$strategy_script"\
        "$strategy_name"
}

