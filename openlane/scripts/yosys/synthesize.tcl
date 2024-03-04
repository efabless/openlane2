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
#
yosys -import

source $::env(SCRIPTS_DIR)/yosys/common.tcl

set report_dir $::env(STEP_DIR)/reports
file mkdir $report_dir

# inputs expected as env vars
set vtop $::env(DESIGN_NAME)

source $::env(_DEPS_SCRIPT)

set lib_args [list]
foreach lib $::env(SYNTH_LIBS) {
    lappend lib_args -liberty $lib
}

if {[info exists ::env(DFF_LIB_SYNTH)]} {
    set dfflib $::env(DFF_LIB_SYNTH)
} else {
    set dfflib $::env(SYNTH_LIBS)
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

# Mapping parameters
set A_factor  0.00
set B_factor  0.88
set F_factor  0.00


# Create SDC File
set sdc_file $::env(STEP_DIR)/synthesis.sdc
set outfile [open ${sdc_file} w]
puts $outfile "set_driving_cell $::env(SYNTH_DRIVING_CELL)"
puts $outfile "set_load $::env(OUTPUT_CAP_LOAD)"
close $outfile


# Assemble Scripts (By Strategy)
set abc_rs_K    "resub,-K,"
set abc_rs      "resub"
set abc_rsz     "resub,-z"
set abc_rf      "drf,-l"
set abc_rfz     "drf,-l,-z"
set abc_rw      "drw,-l"
set abc_rwz     "drw,-l,-z"
set abc_rw_K    "drw,-l,-K"
if { $::env(SYNTH_ABC_LEGACY_REFACTOR) == "1" } {
    set abc_rf      "refactor"
    set abc_rfz     "refactor,-z"
}
if { $::env(SYNTH_ABC_LEGACY_REWRITE) == "1" } {
    set abc_rw      "rewrite"
    set abc_rwz     "rewrite,-z"
    set abc_rw_K    "rewrite,-K"
}
set abc_b       "balance"

set abc_resyn2        "${abc_b}; ${abc_rw}; ${abc_rf}; ${abc_b}; ${abc_rw}; ${abc_rwz}; ${abc_b}; ${abc_rfz}; ${abc_rwz}; ${abc_b}"
set abc_share         "strash; multi,-m; ${abc_resyn2}"
set abc_resyn2a       "${abc_b};${abc_rw};${abc_b};${abc_rw};${abc_rwz};${abc_b};${abc_rwz};${abc_b}"
set abc_resyn3        "balance;resub;resub,-K,6;balance;resub,-z;resub,-z,-K,6;balance;resub,-z,-K,5;balance"
set abc_resyn2rs      "${abc_b};${abc_rs_K},6;${abc_rw};${abc_rs_K},6,-N,2;${abc_rf};${abc_rs_K},8;${abc_rw};${abc_rs_K},10;${abc_rwz};${abc_rs_K},10,-N,2;${abc_b},${abc_rs_K},12;${abc_rfz};${abc_rs_K},12,-N,2;${abc_rwz};${abc_b}"

set abc_choice        "fraig_store; ${abc_resyn2}; fraig_store; ${abc_resyn2}; fraig_store; fraig_restore"
set abc_choice2      "fraig_store; balance; fraig_store; ${abc_resyn2}; fraig_store; ${abc_resyn2}; fraig_store; ${abc_resyn2}; fraig_store; fraig_restore"

set abc_map_old_cnt			"map,-p,-a,-B,0.2,-A,0.9,-M,0"
set abc_map_old_dly         "map,-p,-B,0.2,-A,0.9,-M,0"
set abc_retime_area         "retime,-D,{D},-M,5"
set abc_retime_dly          "retime,-D,{D},-M,6"
set abc_map_new_area        "amap,-m,-Q,0.1,-F,20,-A,20,-C,5000"

set abc_area_recovery_1       "${abc_choice}; map;"
set abc_area_recovery_2       "${abc_choice2}; map;"

set map_old_cnt			    "map,-p,-a,-B,0.2,-A,0.9,-M,0"
set map_old_dly			    "map,-p,-B,0.2,-A,0.9,-M,0"
set abc_retime_area   	"retime,-D,{D},-M,5"
set abc_retime_dly    	"retime,-D,{D},-M,6"
set abc_map_new_area  	"amap,-m,-Q,0.1,-F,20,-A,20,-C,5000"

if { $::env(SYNTH_ABC_BUFFERING) == 1 } {
    set max_tr_arg ""
    if { $max_TR != 0 } {
        set max_tr_arg ",-S,${max_TR}"
    }
    set abc_fine_tune		"buffer,-N,${max_FO}${max_tr_arg};upsize,{D};dnsize,{D}"
} elseif {$::env(SYNTH_SIZING)} {
    set abc_fine_tune       "upsize,{D};dnsize,{D}"
} else {
    set abc_fine_tune       ""
}


set delay_scripts [list \
    "+read_constr,${sdc_file};fx;mfs;strash;${abc_rf};${abc_resyn2};${abc_retime_dly}; scleanup;${abc_map_old_dly};retime,-D,{D};&get,-n;&st;&dch;&nf;&put;${abc_fine_tune};stime,-p;print_stats -m" \
    \
    "+read_constr,${sdc_file};fx;mfs;strash;${abc_rf};${abc_resyn2};${abc_retime_dly}; scleanup;${abc_choice2};${abc_map_old_dly};${abc_area_recovery_2}; retime,-D,{D};&get,-n;&st;&dch;&nf;&put;${abc_fine_tune};stime,-p;print_stats -m" \
    \
    "+read_constr,${sdc_file};fx;mfs;strash;${abc_rf};${abc_resyn2};${abc_retime_dly}; scleanup;${abc_choice};${abc_map_old_dly};${abc_area_recovery_1}; retime,-D,{D};&get,-n;&st;&dch;&nf;&put;${abc_fine_tune};stime,-p;print_stats -m" \
    \
    "+read_constr,${sdc_file};fx;mfs;strash;${abc_rf};${abc_resyn2};${abc_retime_area};scleanup;${abc_choice2};${abc_map_new_area};${abc_choice2};${abc_map_old_dly};retime,-D,{D};&get,-n;&st;&dch;&nf;&put;${abc_fine_tune};stime,-p;print_stats -m" \
    "+read_constr,${sdc_file};&get -n;&st;&dch;&nf;&put;&get -n;&st;&syn2;&if -g -K 6;&synch2;&nf;&put;&get -n;&st;&syn2;&if -g -K 6;&synch2;&nf;&put;&get -n;&st;&syn2;&if -g -K 6;&synch2;&nf;&put;&get -n;&st;&syn2;&if -g -K 6;&synch2;&nf;&put;&get -n;&st;&syn2;&if -g -K 6;&synch2;&nf;&put;buffer -c -N ${max_FO};topo;stime -c;upsize -c;dnsize -c;;stime,-p;print_stats -m" \
]

set area_scripts [list \
    "+read_constr,${sdc_file};fx;mfs;strash;${abc_rf};${abc_resyn2};${abc_retime_area};scleanup;${abc_choice2};${abc_map_new_area};retime,-D,{D};&get,-n;&st;&dch;&nf;&put;${abc_fine_tune};stime,-p;print_stats -m" \
    \
    "+read_constr,${sdc_file};fx;mfs;strash;${abc_rf};${abc_resyn2};${abc_retime_area};scleanup;${abc_choice2};${abc_map_new_area};${abc_choice2};${abc_map_new_area};retime,-D,{D};&get,-n;&st;&dch;&nf;&put;${abc_fine_tune};stime,-p;print_stats -m" \
    \
    "+read_constr,${sdc_file};fx;mfs;strash;${abc_rf};${abc_choice2};${abc_retime_area};scleanup;${abc_choice2};${abc_map_new_area};${abc_choice2};${abc_map_new_area};retime,-D,{D};&get,-n;&st;&dch;&nf;&put;${abc_fine_tune};stime,-p;print_stats -m" \
    "+read_constr,${sdc_file};strash;dch;map -B 0.9;topo;stime -c;buffer -c -N ${max_FO};upsize -c;dnsize -c;stime,-p;print_stats -m" \
]

set all_scripts [list {*}$delay_scripts {*}$area_scripts]

set strategy_parts [split $::env(SYNTH_STRATEGY)]

proc synth_strategy_format_err { } {
    upvar area_scripts area_scripts
    upvar delay_scripts delay_scripts
    log -stderr "\[ERROR] Misformatted SYNTH_STRATEGY (\"$::env(SYNTH_STRATEGY)\")."
    log -stderr "\[ERROR] Correct format is \"DELAY 0-[expr [llength $delay_scripts]-1]|AREA 0-[expr [llength $area_scripts]-1]\"."
    exit 1
}

if { [llength $strategy_parts] != 2 } {
    synth_strategy_format_err
}

set strategy_type [lindex $strategy_parts 0]
set strategy_type_idx [lindex $strategy_parts 1]

if { $strategy_type != "AREA" && $strategy_type != "DELAY" } {
    log -stderr "\[ERROR] AREA|DELAY tokens not found. ($strategy_type)"
    synth_strategy_format_err
}

if { $strategy_type == "DELAY" && $strategy_type_idx >= [llength $delay_scripts] } {
    log -stderr "\[ERROR] strategy index ($strategy_type_idx) is too high."
    synth_strategy_format_err
}

if { $strategy_type == "AREA" && $strategy_type_idx >= [llength $area_scripts] } {
    log -stderr "\[ERROR] strategy index ($strategy_type_idx) is too high."
    synth_strategy_format_err
}

if { $strategy_type == "DELAY" } {
    set strategy_script [lindex $delay_scripts $strategy_type_idx]
    set strategy_name "DELAY $strategy_type_idx"
} else {
    set strategy_script [lindex $area_scripts $strategy_type_idx]
    set strategy_name "AREA $strategy_type_idx"
}

# Get Adder Type
set adder_type $::env(SYNTH_ADDER_TYPE)
if { !($adder_type in [list "YOSYS" "FA" "RCA" "CSA"]) } {
    log -stderr "\[ERROR] Misformatted SYNTH_ADDER_TYPE (\"$::env(SYNTH_ADDER_TYPE)\")."
    log -stderr "\[ERROR] Correct format is \"YOSYS|FA|RCA|CSA\"."
    exit 1
}

# Start Synthesis
if { [info exists ::env(VERILOG_FILES) ]} {
    read_verilog_files $vtop
} elseif { [info exists ::env(VHDL_FILES)] } {
    ghdl {*}$::env(VHDL_FILES) -e $::env(DESIGN_NAME)
} else {
    puts "SCRIPT NOT CALLED CORRECTLY: EITHER VERILOG_FILES OR VHDL_FILES MUST BE SET"
    exit -1
}

if { [info exists ::env(SYNTH_PARAMETERS) ] } {
    foreach define $::env(SYNTH_PARAMETERS) {
        set param_and_value [split $define "="]
        lassign $param_and_value param value
        chparam -set $param $value $vtop
    }
}

select -module $vtop
catch {show -format dot -prefix $::env(STEP_DIR)/hierarchy}
select -clear
hierarchy -check -top $vtop
yosys rename -top $vtop

if { $::env(SYNTH_ELABORATE_ONLY) } {
    yosys proc
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

# Infer tri-state buffers.
set tbuf_map false
if { [info exists ::env(SYNTH_TRISTATE_MAP)] } {
    set tbuf_map true
    tribuf
}

# Handle technology mapping of RCS/CSA adders
if { $adder_type == "RCA"} {
    if { [info exists ::env(SYNTH_RCA_MAP)] } {
        log "\[INFO] Applying ripple carry adder mapping from '$::env(RIPPLE_CARRY_ADDER_MAP)'…"
        techmap -map $::env(RIPPLE_CARRY_ADDER_MAP)
    }
} elseif { $adder_type == "CSA"} {
    if { [info exists ::env(SYNTH_CSA_MAP)] } {
        log "\[INFO] Applying carry-select adder mapping from '$::env(SYNTH_CSA_MAP)'…"
        techmap -map $::env(SYNTH_CSA_MAP)
    }
}

hierarchy -check -auto-top

if { [info exists ::env(_LIGHTER_DFF_MAP)] } {
    puts "Using Lighter with map '$::env(_LIGHTER_DFF_MAP)'…"
    reg_clock_gating -map $::env(_LIGHTER_DFF_MAP)
}

proc_clean
proc_rmdead
proc_prune
proc_init
proc_arst
proc_rom
proc_mux
tee -o "$report_dir/latch.rpt" proc_dlatch
proc_dff
proc_memwr
proc_clean
tee -o "$report_dir/pre_synth_chk.rpt" check
opt_expr
if { $::env(SYNTH_NO_FLAT) != 1 } {
    flatten
}
opt_expr
opt_clean
opt -nodffe -nosdff
fsm
opt
wreduce
peepopt
opt_clean
alumacc
share
opt
memory -nomap
opt_clean
opt -fast -full
memory_map
opt -full
techmap
opt -fast
abc -fast
opt -fast
hierarchy -check
stat
check
delete t:\$print

if { [info exists ::env(SYNTH_EXTRA_MAPPING_FILE)] } {
    log "\[INFO] Applying extra mappings from '$::env(SYNTH_EXTRA_MAPPING_FILE)'…"
    techmap -map $::env(SYNTH_EXTRA_MAPPING_FILE)
}

catch {show -format dot -prefix $::env(STEP_DIR)/post_techmap}

if { $::env(SYNTH_SHARE_RESOURCES) } {
    share -aggressive
}

set fa_map false
if { $adder_type == "FA" } {
    if { [info exists ::env(SYNTH_FA_MAP)] } {
        extract_fa -fa -v
        extract_fa -ha -v
        set fa_map true
    }
}

opt
opt_clean -purge

tee -o "$report_dir/pre_techmap.json" stat -json {*}$lib_args
tee -o "$report_dir/pre_techmap.log" stat {*}$lib_args

# Map tri-state buffers
if { $tbuf_map } {
    log {mapping tbuf}
    log "\[INFO] Applying tri-state buffer mapping from '$::env(SYNTH_TRISTATE_MAP)'…"
    techmap -map $::env(SYNTH_TRISTATE_MAP)
    simplemap
}

# Map full adders
if { $fa_map } {
    log "\[INFO] Applying full-adder mapping from '$::env(FULL_ADDER_MAP)'…"
    techmap -map $::env(FULL_ADDER_MAP)
}

# Handle technology mapping of latches
if { [info exists ::env(SYNTH_LATCH_MAP)] } {
    log "\[INFO] Applying latch mapping from '$::env(SYNTH_LATCH_MAP)'…"
    techmap -map $::env(SYNTH_LATCH_MAP)
    simplemap
}

dfflibmap {*}$dfflib_args
tee -o "$report_dir/post_dff.json" stat -json {*}$lib_args
tee -o "$report_dir/post_dff.log" stat {*}$lib_args

proc run_strategy {output script strategy_name {postfix_with_strategy 0}} {
    upvar clock_period clock_period
    upvar sdc_file sdc_file
    upvar report_dir report_dir
    upvar lib_args lib_args

    log "\[INFO\] USING STRATEGY $strategy_name"

    set strategy_escaped [string map {" " _} $strategy_name]

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
        # Generate public names for the various nets, resulting in very long names that include
        # the full heirarchy, which is preferable to the internal names that are simply
        # sequential numbers such as `_000019_`. Renamed net names can be very long, such as:
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

