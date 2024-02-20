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
proc read_verilog_files {top_module} {
    set verilog_include_args [list]
    if {[info exist ::env(VERILOG_INCLUDE_DIRS)]} {
        foreach dir $::env(VERILOG_INCLUDE_DIRS) {
            lappend verilog_include_args "-I$dir"
        }
    }

    set synlig_params [list]

    if { [info exists ::env(SYNTH_PARAMETERS) ] } {
        foreach define $::env(SYNTH_PARAMETERS) {
            set param_and_value [split $define "="]
            lassign $param_and_value param value
            lappend synlig_params "-P$param=$value"
        }
    }

    if { $::env(USE_SYNLIG) && $::env(SYNLIG_DEFER) } {
        foreach file $::env(VERILOG_FILES) {
            read_systemverilog -defer {*}$::_synlig_defines -sverilog {*}$verilog_include_args $file
        }
        read_systemverilog -link -top $::env(DESIGN_NAME) {*}$synlig_params
    } elseif { $::env(USE_SYNLIG) } {
        read_systemverilog -top $::env(DESIGN_NAME) {*}$::_synlig_defines {*}$synlig_params -sverilog {*}$verilog_include_args {*}$::env(VERILOG_FILES)
    } else {
        foreach file $::env(VERILOG_FILES) {
            read_verilog -sv {*}$verilog_include_args $file
        }

        if { [info exists ::env(SYNTH_PARAMETERS) ] } {
            foreach define $::env(SYNTH_PARAMETERS) {
                set param_and_value [split $define "="]
                lassign $param_and_value param value
                chparam -set $param $value $top_module
            }
        }
    }
}
