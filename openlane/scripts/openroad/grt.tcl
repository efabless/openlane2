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
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read

set_propagated_clock [all_clocks]

if { $::env(GRT_REPAIR_ANTENNAE) } {
    set diode_split [split $::env(DIODE_CELL) "/"]
    set_placement_padding -masters [lindex $diode_split 0] -left $::env(DIODE_PADDING)
}

source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl

# Check Antennae (Pre-Repair)
puts "%OL_CREATE_REPORT antenna.rpt"
check_antennas -verbose
puts "%OL_END_REPORT"

if { $::env(GRT_REPAIR_ANTENNAE) } {
    repair_antennas "[lindex $diode_split 0]" -iterations $::env(GRT_ANT_ITERS)
    check_placement

    # Check Antennae (Post-Repair)
    puts "%OL_CREATE_REPORT antenna_after.rpt"
    check_antennas -verbose
    puts "%OL_END_REPORT"
}

write

if {[info exists ::env(CLOCK_PORT)]} {
    if { $::env(GRT_ESTIMATE_PARASITICS) == 1 } {
        # set rc values
        source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl
        # estimate wire rc parasitics
        estimate_parasitics -global_routing

        set ::env(RUN_STANDALONE) 0
        source $::env(SCRIPTS_DIR)/openroad/sta.tcl
    }
} else {
    puts "\[WARN\]: No CLOCK_PORT found. Skipping STA…"
}
