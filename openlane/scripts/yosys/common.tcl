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

#  Parts of this file adapted from https://github.com/YosysHQ/yosys/blob/master/techlibs/common/synth.cc
#
#  Copyright (C) 2012  Claire Xenia Wolf <claire@yosyshq.com>
#
#  Permission to use, copy, modify, and/or distribute this software for any
#  purpose with or without fee is hereby granted, provided that the above
#  copyright notice and this permission notice appear in all copies.
#
#  THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
#  WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
#  MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
#  ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
#  WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
#  ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
#  OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
source $::env(_TCL_ENV_IN)

namespace eval yosys_ol {
    proc ol_proc {report_dir} {
        proc_clean
        proc_rmdead
        proc_prune
        proc_init
        proc_arst
        proc_rom
        proc_mux
        tee -o "$report_dir/latch.rpt" proc_dlatch
        proc_dff
        proc_memwr
        proc_clean
        tee -o "$report_dir/pre_synth_chk.rpt" check
        opt_expr
    }

    proc ol_synth {design_name report_dir} {
        hierarchy -check -top $design_name -nokeep_prints -nokeep_asserts
        yosys_ol::ol_proc $report_dir
        if { $::env(SYNTH_NO_FLAT) != 1 } {
            flatten
        }
        opt_expr
        opt_clean
        opt -nodffe -nosdff
        fsm
        opt
        wreduce
        peepopt
        opt_clean
        alumacc
        share
        opt
        memory -nomap
        opt_clean

        opt -fast -full
        memory_map
        opt -full
        techmap
        opt -fast
        abc -fast
        opt -fast
        hierarchy -check -nokeep_prints -nokeep_asserts
        stat
        check
    }

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
                read_verilog -noautowire -sv {*}$verilog_include_args $file
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
}

