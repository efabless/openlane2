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


source $::env(SCRIPTS_DIR)/openroad/common/set_routing_layers.tcl
source $::env(SCRIPTS_DIR)/openroad/common/set_layer_adjustments.tcl
set_macro_extension $::env(GRT_MACRO_EXTENSION)

set diode_split [split $::env(DIODE_CELL) "/"]
set_placement_padding -masters [lindex $diode_split 0] -left $::env(DIODE_PADDING)
repair_antennas "[lindex $diode_split 0]" -iterations $::env(GRT_ANT_ITERS)
check_placement

# start checking antennas and generate a detailed report
puts "%OL_CREATE_REPORT antennae.rpt"
check_antennas -verbose
puts "%OL_END_REPORT"

write