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

unset_propagated_clock [all_clocks]

# set don't touch nets
source $::env(SCRIPTS_DIR)/openroad/common/resizer.tcl
set_dont_touch_rx "$::env(RSZ_DONT_TOUCH_RX)"

# set don't use cells
if { [info exists ::env(RSZ_DONT_USE_CELLS)] } {
    set_dont_use $::env(RSZ_DONT_USE_CELLS)
}

# set rc values
source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl

# CTS and detailed placement move instances, so update parastic estimates.
# estimate wire rc parasitics
estimate_parasitics -placement


# Buffer I/O
if { $::env(DESIGN_REPAIR_BUFFER_INPUT_PORTS) } {
    buffer_ports -inputs
}

if { $::env(DESIGN_REPAIR_BUFFER_OUTPUT_PORTS) } {
    buffer_ports -outputs
}

# Repair Design
repair_design\
    -max_wire_length $::env(DESIGN_REPAIR_MAX_WIRE_LENGTH) \
    -slew_margin $::env(DESIGN_REPAIR_MAX_SLEW_PCT) \
    -cap_margin $::env(DESIGN_REPAIR_MAX_CAP_PCT)

if { $::env(DESIGN_REPAIR_TIE_FANOUT) } {
    # repair tie lo fanout
    repair_tie_fanout -separation $::env(DESIGN_REPAIR_TIE_SEPARATION) $::env(SYNTH_TIELO_CELL)
    # repair tie hi fanout
    repair_tie_fanout -separation $::env(DESIGN_REPAIR_TIE_SEPARATION) $::env(SYNTH_TIEHI_CELL)
}

report_floating_nets -verbose

# Legalize
source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl

if { [catch {check_placement -verbose} errmsg] } {
    puts stderr $errmsg
    exit 1
}

unset_dont_touch_rx "$::env(RSZ_DONT_TOUCH_RX)"

source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl
estimate_parasitics -placement

write
