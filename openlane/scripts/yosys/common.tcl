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
proc read_deps {{power_defines 0} {macro_libs 1} {extra_libs 1}} {
    if { [info exists ::env(VERILOG_DEFINES)] } {
        foreach define $::env(VERILOG_DEFINES) {
            log "Defining ${define}…"
            verilog_defines -D$define
        }
    }

    if { [info exists ::env(VERILOG_POWER_DEFINE)] && $power_defines } {
        log "Defining $::env(VERILOG_POWER_DEFINE)…"
        verilog_defines -D$::env(VERILOG_POWER_DEFINE)
    }

    foreach lib $::env(FULL_LIBS) {
        log "Reading SCL library '$lib' as a blackbox…"
        read_liberty -lib -ignore_miss_dir -setattr blackbox $lib
    }

    if { [info exists ::env(MACRO_LIBS)] && $macro_libs } {
        foreach lib $::env(MACRO_LIBS) {
            log "Reading macro library '$lib' as a black-box…"
            read_liberty -lib -ignore_miss_dir -setattr blackbox $lib
        }
    }

    if { [info exists ::env(EXTRA_LIBS)] && $extra_libs } {
        foreach lib $::env(EXTRA_LIBS) {
            log "Reading extra library '$lib' as a black-box…"
            read_liberty -lib -ignore_miss_dir -setattr blackbox $lib
        }
    }

    set verilog_include_args [list]
    if {[info exist ::env(VERILOG_INCLUDE_DIRS)]} {
        foreach dir $::env(VERILOG_INCLUDE_DIRS) {
            lappend verilog_include_args "-I$dir"
        }
    }

    if { [info exists ::env(MACRO_NLS)] } {
        foreach nl $::env(MACRO_NLS) {
            log "Reading macro netlist '$nl' as a black-box…"
            read_verilog -sv -lib {*}$verilog_include_args $nl
        }
    }

    if { [info exists ::env(EXTRA_VERILOG_MODELS)] } {
        foreach nl $::env(EXTRA_VERILOG_MODELS) {
            log "Reading extra model '$nl' as a black-box…"
            read_verilog -sv -lib {*}$verilog_include_args $nl
        }
    }
}
