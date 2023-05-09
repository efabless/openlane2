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
set vtop $::env(DESIGN_NAME)

read_deps "on"

set verilog_include_args [list]
if {[info exist ::env(VERILOG_INCLUDE_DIRS)]} {
    foreach dir $::env(VERILOG_INCLUDE_DIRS) {
        lappend verilog_include_args "-I$dir"
    }
}
for { set i 0 } { $i < [llength $::env(VERILOG_FILES)] } { incr i } {
    read_verilog -sv {*}$verilog_include_args [lindex $::env(VERILOG_FILES) $i]
}
select -module $vtop
yosys proc
json -o $::env(SAVE_JSON_HEADER)
