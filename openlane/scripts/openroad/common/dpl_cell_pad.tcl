# Copyright 2022 Efabless Corporation
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
set cell_pad_value $::env(DPL_CELL_PADDING)

set cell_pad_side [expr $cell_pad_value / 2]

set_placement_padding -global -right $cell_pad_side -left $cell_pad_side

foreach wildcard $::env(CELL_PAD_EXCLUDE) {
    set_placement_padding -masters $wildcard -right 0 -left 0
}
if { [info exists ::env(DIODE_PADDING)] && $::env(DIODE_PADDING) } {
    set diode_split [split $::env(DIODE_CELL) "/"]
    set_placement_padding -masters [lindex $diode_split 0] -left $::env(DIODE_PADDING)
}