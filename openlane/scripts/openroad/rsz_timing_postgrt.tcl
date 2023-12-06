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
source $::env(SCRIPTS_DIR)/openroad/common/resizer.tcl

load_rsz_corners
read_current_odb

set_propagated_clock [all_clocks]

set_dont_touch_objects

# set rc values
source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl

# (Re-)GRT and Estimate Parasitics
source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl
estimate_parasitics -global_routing

# Resize
repair_timing -setup \
    -setup_margin $::env(GRT_RESIZER_SETUP_SLACK_MARGIN) \
    -max_buffer_percent $::env(GRT_RESIZER_SETUP_MAX_BUFFER_PCT)

set arg_list [list]
lappend arg_list -hold
lappend arg_list -setup_margin $::env(GRT_RESIZER_SETUP_SLACK_MARGIN)
lappend arg_list -hold_margin $::env(GRT_RESIZER_HOLD_SLACK_MARGIN)
lappend arg_list -max_buffer_percent $::env(GRT_RESIZER_HOLD_MAX_BUFFER_PCT)
if { $::env(GRT_RESIZER_ALLOW_SETUP_VIOS) == 1 } {
    lappend arg_list -allow_setup_violations
}
if { $::env(GRT_RESIZER_GATE_CLONING) != 1 } {
    lappend arg_list -skip_gate_cloning
}
repair_timing {*}$arg_list

# Re-DPL and GRT
source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl
unset_dont_touch_objects
source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl

write_views

report_design_area_metrics

