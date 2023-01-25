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

if { ![info exists ::env(STA_PRE_CTS)] } {
    set ::env(STA_PRE_CTS) {0}
}

if { $::env(RUN_STANDALONE) == 1 } {
    source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
    if { [info exists ::env(CURRENT_ODB)] } {
        read
    } else {
        read_libs
        read_lef $::env(TECH_LEF)
        foreach lef $::env(CELLS_LEF) {
            read_lef $lef
        }
        read_netlist
    }

    if { $::env(STA_PRE_CTS) == 1 } {
        unset_propagated_clock [all_clocks]
    } else {
        set_propagated_clock [all_clocks]
    }
}

set_cmd_units -time ns -capacitance pF -current mA -voltage V -resistance kOhm -distance um

if { [info exists ::env(CURRENT_SPEF)] } {
    read_spef $::env(CURRENT_SPEF)
}

puts "%OL_CREATE_REPORT min.rpt"
puts "==========================================================================="
puts "report_checks -path_delay min (Hold)"
puts "============================================================================"
report_checks -path_delay min -fields {slew cap input nets fanout} -format full_clock_expanded -group_count 5
puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT max.rpt"
puts "==========================================================================="
puts "report_checks -path_delay max (Setup)"
puts "============================================================================"
report_checks -path_delay max -fields {slew cap input nets fanout} -format full_clock_expanded -group_count 5
puts "%OL_END_REPORT"


puts "%OL_CREATE_REPORT checks.rpt"
puts "==========================================================================="
puts "report_checks -unconstrained"
puts "============================================================================"
report_checks -unconstrained -fields {slew cap input nets fanout} -format full_clock_expanded

puts "==========================================================================="
puts "report_checks --slack_max -0.01"
puts "============================================================================"
report_checks -slack_max -0.01 -fields {slew cap input nets fanout} -format full_clock_expanded
puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT parasitics_annotation.rpt"
puts "==========================================================================="
puts "report_parasitic_annotation -report_unannotated"
puts "============================================================================"
report_parasitic_annotation -report_unannotated
puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT slew.rpt"
puts "==========================================================================="
puts " report_check_types -max_slew -max_cap -max_fanout -violators"
puts "============================================================================"
report_check_types -max_slew -max_cap -max_fanout -violators
puts "%OL_END_REPORT"

sta::report_tns_metric -setup
sta::report_tns_metric -hold
sta::report_worst_slack_metric -setup
sta::report_worst_slack_metric -hold
sta::report_erc_metrics
sta::report_power_metric
sta::report_design_area_metrics

# report clock skew if the clock port is defined
# OR hangs if this command is run on clockless designs
if { [info exists ::env(CLOCK_PORT)] } {
    sta::report_clock_skew_metric -setup
    sta::report_clock_skew_metric -hold
}

write
