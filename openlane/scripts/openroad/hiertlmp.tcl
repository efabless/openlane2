# Copyright 2024 Efabless Corporation
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

# Code adapted from OpenROAD Flow Scripts under the following license:
#
# BSD 3-Clause License
#
# Copyright (c) 2018-2023, The Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb

if { [llength [find_unfixed_macros]] } {
    report_design_area_metrics
    set rtlmp_args [list]
    file mkdir $::env(STEP_DIR)/reports

    lappend rtlmp_args -report_directory $::env(STEP_DIR)/reports
    lappend rtlmp_args -halo_width $::env(FP_MACRO_HORIZONTAL_HALO)
    lappend rtlmp_args -halo_height $::env(FP_MACRO_VERTICAL_HALO)

    if { [info exists ::env(RTLMP_MAX_LEVEL)]} {
        lappend rtlmp_args -max_num_level $::env(RTLMP_MAX_LEVEL)
    }
    if { [info exists ::env(RTLMP_MAX_INST)]} {
        lappend rtlmp_args -max_num_inst $::env(RTLMP_MAX_INST)
    }
    if { [info exists ::env(RTLMP_MIN_INST)]} {
        lappend rtlmp_args -min_num_inst $::env(RTLMP_MIN_INST)
    }
    if { [info exists ::env(RTLMP_MAX_MACRO)]} {
        lappend rtlmp_args -max_num_macro $::env(RTLMP_MAX_MACRO)
    }
    if { [info exists ::env(RTLMP_MIN_MACRO)]} {
        lappend rtlmp_args -min_num_macro $::env(RTLMP_MIN_MACRO)
    }

    if { [info exists ::env(RTLMP_MIN_AR)]} {
        lappend rtlmp_args -min_ar $::env(RTLMP_MIN_AR)
    }
    if { [info exists ::env(RTLMP_SIGNATURE_NET_THRESHOLD)]} {
        lappend rtlmp_args -signature_net_threshold $::env(RTLMP_SIGNATURE_NET_THRESHOLD)
    }
    if { [info exists ::env(RTLMP_AREA_WT)]} {
        lappend rtlmp_args -area_weight $::env(RTLMP_AREA_WT)
    }
    if { [info exists ::env(RTLMP_WIRELENGTH_WT)]} {
        lappend rtlmp_args -wirelength_weight $::env(RTLMP_WIRELENGTH_WT)
    }
    if { [info exists ::env(RTLMP_OUTLINE_WT)]} {
        lappend rtlmp_args -outline_weight $::env(RTLMP_OUTLINE_WT)
    }
    if { [info exists ::env(RTLMP_BOUNDARY_WT)]} {
        lappend rtlmp_args -boundary_weight $::env(RTLMP_BOUNDARY_WT)
    }

    if { [info exists ::env(RTLMP_NOTCH_WT)]} {
        lappend rtlmp_args -notch_weight $::env(RTLMP_NOTCH_WT)
    }

    if { [info exists ::env(RTLMP_DEAD_SPACE)]} {
        lappend rtlmp_args -dead_space $::env(RTLMP_DEAD_SPACE)
    }

    if { [info exists ::env(RTLMP_FENCE_LX)]} {
        lappend rtlmp_args -fence_lx $::env(RTLMP_FENCE_LX)
    }
    if { [info exists ::env(RTLMP_FENCE_LY)]} {
        lappend rtlmp_args -fence_ly $::env(RTLMP_FENCE_LY)
    }
    if { [info exists ::env(RTLMP_FENCE_UX)]} {
        lappend rtlmp_args -fence_ux $::env(RTLMP_FENCE_UX)
    }
    if { [info exists ::env(RTLMP_FENCE_UY)]} {
        lappend rtlmp_args -fence_uy $::env(RTLMP_FENCE_UY)
    }

    log_cmd rtl_macro_placer {*}$rtlmp_args
} else {
    puts "\[INFO\] No macro instances found that are not 'FIXED'."
}

write_views

report_design_area_metrics
