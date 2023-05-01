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
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl

set arg_list [list]
lappend arg_list -typical $::env(LIB_TYPICAL)
if { [info exists ::env(STA_MULTICORNER)] && $::env(STA_MULTICORNER) } {
    lappend arg_list -fastest $::env(LIB_FASTEST)
    lappend arg_list -slowest $::env(LIB_SLOWEST)
}
read_libs {*}$arg_list

set report_dir "."
if { [info exists ::env(PROCESS_CORNER)] } {
    set report_dir "$::env(PROCESS_CORNER)"
}

if { [file tail [info nameofexecutable]] == "sta" } {
    # OpenSTA
    read_netlist -all
    read_spefs
} else {
    # OpenROAD
    read
    if { [info exists ::env(ESTIMATE_PARASITICS)]} {
        estimate_parasitics {*}$::env(ESTIMATE_PARASITICS)
    }
}

set_cmd_units -time ns -capacitance pF -current mA -voltage V -resistance kOhm -distance um

if { [info exists ::env(STA_PRE_CTS)] && $::env(STA_PRE_CTS) == 1 } {
    unset_propagated_clock [all_clocks]
} else {
    set_propagated_clock [all_clocks]
}

puts "%OL_CREATE_REPORT $report_dir/min.rpt"
puts "\n==========================================================================="
puts "report_checks -path_delay min (Hold)"
puts "============================================================================"
foreach corner [sta::corners] {
    puts "======================= [$corner name] Corner ===================================\n"
    report_checks -sort_by_slack -path_delay min -fields {slew cap input nets fanout} -format full_clock_expanded -group_count 1000 -corner [$corner name]
    puts ""
}
puts "%OL_END_REPORT"


puts "%OL_CREATE_REPORT $report_dir/max.rpt"
puts "\n==========================================================================="
puts "report_checks -path_delay max (Setup)"
puts "============================================================================"
foreach corner [sta::corners] {
    puts "======================= [$corner name] Corner ===================================\n"
    report_checks -sort_by_slack -path_delay max -fields {slew cap input nets fanout} -format full_clock_expanded -group_count 1000 -corner [$corner name]
    puts ""
}
puts "%OL_END_REPORT"


puts "%OL_CREATE_REPORT $report_dir/checks.rpt"
puts "\n==========================================================================="
puts "report_checks -unconstrained"
puts "==========================================================================="
foreach corner [sta::corners] {
    puts "======================= [$corner name] Corner ===================================\n"
    report_checks -unconstrained -fields {slew cap input nets fanout} -format full_clock_expanded -corner [$corner name]
    puts ""
}


puts "\n==========================================================================="
puts "report_checks --slack_max -0.01"
puts "============================================================================"
foreach corner [sta::corners] {
    puts "======================= [$corner name] Corner ===================================\n"
    report_checks -slack_max -0.01 -fields {slew cap input nets fanout} -format full_clock_expanded -corner [$corner name]
    puts ""
}

puts "\n==========================================================================="
puts " report_check_types -max_slew -max_cap -max_fanout -violators"
puts "============================================================================"
foreach corner [sta::corners] {
    puts "======================= [$corner name] Corner ===================================\n"
    report_check_types -max_slew -max_capacitance -max_fanout -violators -corner [$corner name]
    puts ""
}

puts "\n==========================================================================="
puts "report_parasitic_annotation -report_unannotated"
puts "============================================================================"
report_parasitic_annotation -report_unannotated

puts "\n==========================================================================="
puts "max slew violation count [sta::max_slew_violation_count]"
puts "max fanout violation count [sta::max_fanout_violation_count]"
puts "max cap violation count [sta::max_capacitance_violation_count]"
puts "============================================================================"

puts "\n==========================================================================="
puts "check_setup -verbose -unconstrained_endpoints -multiple_clock -no_clock -no_input_delay -loops -generated_clocks"
puts "==========================================================================="
check_setup -verbose -unconstrained_endpoints -multiple_clock -no_clock -no_input_delay -loops -generated_clocks
puts "%OL_END_REPORT"



puts "%OL_CREATE_REPORT $report_dir/power.rpt"
puts "\n==========================================================================="
puts " report_power"
puts "============================================================================"
foreach corner [sta::corners] {
    puts "======================= [$corner name] Corner ===================================\n"
    report_power -corner [$corner name]
    puts ""
}
puts "%OL_END_REPORT"

# report clock skew if the clock port is defined
# OR hangs if this command is run on clockless designs
if { $::env(CLOCK_PORT) != "__VIRTUAL_CLK__" && $::env(CLOCK_PORT) != "" } {
    puts "%OL_CREATE_REPORT $report_dir/skew.rpt"
    puts "\n==========================================================================="
    puts "report_clock_skew"
    puts "============================================================================"
    report_clock_skew
    puts "%OL_END_REPORT"
}

puts "%OL_CREATE_REPORT $report_dir/summary.rpt"
puts "\n==========================================================================="
puts "report_tns"
puts "============================================================================"
report_tns

puts "\n==========================================================================="
puts "report_wns"
puts "============================================================================"
report_wns

puts "\n==========================================================================="
puts "report_worst_slack -max (Setup)"
puts "============================================================================"
report_worst_slack -max

puts "\n==========================================================================="
puts "report_worst_slack -min (Hold)"
puts "============================================================================"
report_worst_slack -min
puts "%OL_END_REPORT"

write_libs