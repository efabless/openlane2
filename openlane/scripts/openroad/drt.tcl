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
proc run_drt_antenna_repair_step {i args} {
        set directory "${i}-after-repair-antenna"
        file mkdir ${i}-after-repair-antenna
        set output_drc "-output_drc $::env(STEP_DIR)/$directory/$::env(DESIGN_NAME).drc"
        log_cmd detailed_route {*}$args {*}$output_drc
        if { $::env(DRT_SAVE_SNAPSHOTS) } {
            foreach snapshot [glob -nocomplain drt_iter*.odb] {
                file rename -force $snapshot $directory/[file tail $snapshot]
            }
        }
        foreach drc_file [glob -nocomplain $::env(STEP_DIR)/$directory/*.drc] {
            file copy -force $drc_file $::env(STEP_DIR)/[file tail $drc_file]
        }
        write_db $::env(STEP_DIR)/$directory/$::env(DESIGN_NAME).odb
}

source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb

set_thread_count $::env(DRT_THREADS)

set min_layer $::env(RT_MIN_LAYER)
if { [info exists ::env(DRT_MIN_LAYER)] } {
    set min_layer $::env(DRT_MIN_LAYER)
}

set max_layer $::env(RT_MAX_LAYER)
if { [info exists ::env(DRT_MAX_LAYER)] } {
    set max_layer $::env(DRT_MAX_LAYER)
}
if { $::env(DRT_SAVE_SNAPSHOTS) } {
    set_debug_level DRT snapshot 1
}
set drc_report_iter_step_arg ""
if { $::env(DRT_SAVE_SNAPSHOTS) } {
    set_debug_level DRT snapshot 1
    set drc_report_iter_step_arg "-drc_report_iter_step 1"
}
if { [info exists ::env(DRT_SAVE_DRC_REPORT_ITERS)] } {
    set drc_report_iter_step_arg "-drc_report_iter_step $::env(DRT_SAVE_DRC_REPORT_ITERS)"
}

set args [list]
lappend args -bottom_routing_layer $min_layer
lappend args -top_routing_layer $max_layer
set output_drc "-output_drc $::env(STEP_DIR)/$::env(DESIGN_NAME).drc"
if { $::env(DRT_ANTENNA_REPAIR) } {
    set output_drc "-output_drc $::env(STEP_DIR)/$::env(DESIGN_NAME).drc"
}
lappend args -output_drc $::env(STEP_DIR)/$::env(DESIGN_NAME).drc
lappend args -droute_end_iter $::env(DRT_OPT_ITERS)
lappend args -or_seed 42
lappend args -verbose 1
lappend args {*}$drc_report_iter_step_arg {*}$output_drc

log_cmd detailed_route {*}$args


if { $::env(DRT_ANTENNA_REPAIR) } {
    set i 0
    set has_antenna_vios 1
    set diode_split [split $::env(DIODE_CELL) "/"]
    set has_antenna_vios [log_cmd repair_antennas "[lindex $diode_split 0]" -ratio_margin $::env(DRT_ANTENNA_MARGIN)]
    if {$has_antenna_vios} {
        run_drt_antenna_repair_step $i {*}$args
    }
    incr i
    while {[check_antennas] && $i <= $::env(DRT_ANTENNA_REPAIR_ITERS)} {
        run_drt_antenna_repair_step $i {*}$args
        incr i
    }
}

write_views
