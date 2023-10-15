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
if { $::env(MAGIC_EXT_USE_GDS) } {
    gds read $::env(CURRENT_GDS)
} else {
    source $::env(SCRIPTS_DIR)/magic/common/read.tcl
    read_tech_lef
    read_pdk_lef
    read_macro_lef
    read_extra_lef
    read_def
}

load $::env(DESIGN_NAME) -dereference

set backup $::env(PWD)
set extdir $::env(STEP_DIR)/extraction
set netlist $::env(STEP_DIR)/$::env(DESIGN_NAME).spice

file mkdir $extdir
cd $extdir

extract do local
extract no capacitance
extract no coupling
extract no resistance
extract no adjust
if { ! $::env(MAGIC_NO_EXT_UNIQUE) } {
    extract unique
}
# extract warn all
extract

ext2spice lvs

# For designs where more than one top-level pin is connected to the same net
if { $::env(MAGIC_EXT_SHORT_RESISTOR) } {
    ext2spice short resistor
}

ext2spice -o $netlist $::env(DESIGN_NAME).ext

cd $backup
feedback save $::env(STEP_DIR)/feedback.txt
