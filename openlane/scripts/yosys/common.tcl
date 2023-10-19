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
set ::synlig_defines [list]

proc read_deps {{power_defines "off"}} {
    if { [info exists ::env(VERILOG_DEFINES) ] } {
        foreach define $::env(VERILOG_DEFINES) {
            log "Defining ${define}…"
            verilog_defines -D$define
            lappend ::synlig_defines "+define+$define"
        }
    }

    if { [info exists ::env(VERILOG_POWER_DEFINE)] } {
        if { $power_defines == "on" } {
            log "Defining $::env(VERILOG_POWER_DEFINE)…"
            verilog_defines -D$::env(VERILOG_POWER_DEFINE)
            lappend ::synlig_defines "+define+$::env(VERILOG_POWER_DEFINE)"
        }
    }

    foreach lib $::env(FULL_LIBS) {
        log "Reading SCL library '$lib' as a blackbox…"
        read_liberty -lib -ignore_miss_dir -setattr blackbox $lib
    }

    if { [info exists ::env(MACRO_LIBS) ] } {
        foreach lib $::env(MACRO_LIBS) {
            log "Reading macro library '$lib' as a black-box…"
            read_liberty -lib -ignore_miss_dir -setattr blackbox $lib
        }
    }

    if { [info exists ::env(EXTRA_LIBS) ] } {
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

proc read_verilog_files {} {
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
            read_systemverilog -defer $::synlig_defines -sverilog {*}$verilog_include_args $file
        }
        read_systemverilog -link -top $::env(DESIGN_NAME) {*}$synlig_params
    } elseif { $::env(USE_SYNLIG) } {
        read_systemverilog -top $::env(DESIGN_NAME) $::synlig_defines {*}$synlig_params -sverilog {*}$verilog_include_args {*}$::env(VERILOG_FILES)
    } else {
        foreach file $::env(VERILOG_FILES) {
            read_verilog -sv {*}$verilog_include_args $file
        }

        if { [info exists ::env(SYNTH_PARAMETERS) ] } {
            foreach define $::env(SYNTH_PARAMETERS) {
                set param_and_value [split $define "="]
                lassign $param_and_value param value
                chparam -set $param $value $vtop
            }
        }
    }
}