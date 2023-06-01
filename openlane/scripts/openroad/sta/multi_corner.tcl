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

set_cmd_units\
    -time ns\
    -capacitance pF\
    -current mA\
    -voltage V\
    -resistance kOhm\
    -distance um

set sta_report_default_digits 6


read_timing_info
if { ![info exists ::env(OPENSTA)] || !$::env(OPENSTA) } {
    read_current_odb

    # Internal API- brittle
    if { [grt::have_routes] } {
        estimate_parasitics -global_routing
    } elseif { [rsz::check_corner_wire_cap] } {
        estimate_parasitics -placement
    }
}
read_spefs

set_propagated_clock [all_clocks]

start_metrics_file

puts "%OL_CREATE_REPORT min.rpt"
puts "\n==========================================================================="
puts "report_checks -path_delay min (Hold)"
puts "============================================================================"
foreach corner [sta::corners] {
    puts "======================= [$corner name] Corner ===================================\n"
    report_checks -sort_by_slack -path_delay min -fields {slew cap input nets fanout} -format full_clock_expanded -group_count 1000 -corner [$corner name]
    puts ""
}
puts "%OL_END_REPORT"


puts "%OL_CREATE_REPORT max.rpt"
puts "\n==========================================================================="
puts "report_checks -path_delay max (Setup)"
puts "============================================================================"
foreach corner [sta::corners] {
    puts "======================= [$corner name] Corner ===================================\n"
    report_checks -sort_by_slack -path_delay max -fields {slew cap input nets fanout} -format full_clock_expanded -group_count 1000 -corner [$corner name]
    puts ""
}
puts "%OL_END_REPORT"


puts "%OL_CREATE_REPORT checks.rpt"
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
write_metric_int "clock__max_slew_violation__count" [sta::max_slew_violation_count]
puts "max fanout violation count [sta::max_fanout_violation_count]"
write_metric_int "design__max_fanout_violation__count" [sta::max_fanout_violation_count]
puts "max cap violation count [sta::max_capacitance_violation_count]"
write_metric_int "design__max_cap_violation__count" [sta::max_capacitance_violation_count]
puts "============================================================================"

puts "\n==========================================================================="
puts "check_setup -verbose -unconstrained_endpoints -multiple_clock -no_clock -no_input_delay -loops -generated_clocks"
puts "==========================================================================="
check_setup -verbose -unconstrained_endpoints -multiple_clock -no_clock -no_input_delay -loops -generated_clocks
puts "%OL_END_REPORT"



puts "%OL_CREATE_REPORT power.rpt"
puts "\n==========================================================================="
puts " report_power"
puts "============================================================================"
foreach corner [sta::corners] {
    puts "======================= [$corner name] Corner ===================================\n"
    report_power -corner [$corner name]
    puts ""
}
puts "%OL_END_REPORT"

set clocks [sta::sort_by_name [sta::all_clocks]]
set default_corner [sta::cmd_corner]

puts "%OL_CREATE_REPORT skew.min.rpt"
puts "\n==========================================================================="
puts "Clock Skew (Hold)"
puts "============================================================================"
set skew_design -1e30
foreach corner [sta::corners] {
    sta::set_cmd_corner $corner
    set skew_corner [sta::format_time [sta::worst_clk_skew_cmd "min"] $sta_report_default_digits]
    set skew_design [max $skew_design $skew_corner]

    write_metric_num "clock__skew__worst_hold__corner:[$corner name]" $skew_corner

    puts "======================= [$corner name] Corner ===================================\n"
    report_clock_skew -corner [$corner name] -hold
}
sta::set_cmd_corner $default_corner

write_metric_num "clock__skew__worst_hold" $skew_design
puts "worst overall skew: $skew_design"
puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT skew.max.rpt"
puts "\n==========================================================================="
puts "Clock Skew (Setup)"
puts "============================================================================"
set skew_design -1e30
foreach corner [sta::corners] {
    sta::set_cmd_corner $corner
    set skew_corner [sta::format_time [sta::worst_clk_skew_cmd "max"] $sta_report_default_digits]
    set skew_design [max $skew_design $skew_corner]

    write_metric_num "clock__skew__worst_setup__corner:[$corner name]" $skew_corner

    puts "======================= [$corner name] Corner ===================================\n"
    report_clock_skew -corner [$corner name] -setup
}
sta::set_cmd_corner $default_corner

write_metric_num "clock__skew__worst_setup" $skew_design
puts "worst overall skew: $skew_design"
puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT ws.min.rpt"
puts "\n==========================================================================="
puts "Worst Slack (Hold)"
puts "============================================================================"
set ws_design 1e30
foreach corner [sta::corners] {
    set ws [sta::format_time [sta::worst_slack_corner $corner "min"] $sta_report_default_digits]
    if { $ws < $ws_design } {
        set ws_design $ws
    }
    write_metric_num "timing__hold__ws__corner:[$corner name]" $ws
    puts "[$corner name]: $ws"
}
write_metric_num "timing__hold__ws" $ws_design
puts "design: $ws_design"
puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT ws.max.rpt"
puts "\n==========================================================================="
puts "Worst Slack (Setup)"
puts "============================================================================"
set ws_design 1e30
foreach corner [sta::corners] {
    set ws [sta::format_time [sta::worst_slack_corner $corner "max"] $sta_report_default_digits]
    if { $ws < $ws_design } {
        set ws_design $ws
    }
    write_metric_num "timing__setup__ws__corner:[$corner name]" $ws
    puts "[$corner name]: $ws"
}
write_metric_num "timing__setup__ws" $ws_design
puts "design: $ws_design"
puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT tns.min.rpt"
puts "\n==========================================================================="
puts "Total Negative Slack (Hold)"
puts "============================================================================"
set tns_design 0
foreach corner [sta::corners] {
    set tns [sta::format_time [sta::total_negative_slack_corner_cmd $corner "min"] $sta_report_default_digits]
    set tns_design [expr {$tns + $tns_design}]
    write_metric_num "timing__hold__tns__corner:[$corner name]" $tns
    puts "[$corner name]: $tns"
}
write_metric_num "timing__hold__tns" $tns_design
puts "design: $tns_design"
puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT tns.max.rpt"
puts "\n==========================================================================="
puts "Total Negative Slack (Setup)"
puts "============================================================================"
set tns_design 0
foreach corner [sta::corners] {
    set tns [sta::format_time [sta::total_negative_slack_corner_cmd $corner "max"] $sta_report_default_digits]
    set tns_design [expr {$tns + $tns_design}]
    write_metric_num "timing__setup__tns__corner:[$corner name]" $tns
    puts "[$corner name]: $tns"
}
write_metric_num "timing__setup__tns" $tns_design
puts "design: $tns_design"
puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT wns.min.rpt"
puts "\n==========================================================================="
puts "Worst Negative Slack (Hold)"
puts "============================================================================"
set wns_design 0
foreach corner [sta::corners] {
    set ws [sta::format_time [sta::worst_slack_corner $corner "min"] $sta_report_default_digits]
    set wns 0
    if { $ws < 0 } {
        set wns $ws
    }
    if { $wns < $wns_design } {
        set wns_design $wns
    }
    write_metric_num "timing__hold__wns__corner:[$corner name]" $wns
    puts "[$corner name]: $wns"
}
write_metric_num "timing__hold__wns" $wns_design
puts "design: $wns_design"
puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT wns.max.rpt"
puts "\n==========================================================================="
puts "Worst Negative Slack (Setup)"
puts "============================================================================"
set wns_design 0
foreach corner [sta::corners] {
    set ws [sta::format_time [sta::worst_slack_corner $corner "max"] $sta_report_default_digits]
    set wns 0.0
    if { $ws < 0 } {
        set wns ws
    }
    if { $wns < $wns_design } {
        set wns_design $wns
    }
    write_metric_num "timing__setup__wns__corner:[$corner name]" $wns
    puts "[$corner name]: $wns"
}
write_metric_num "timing__setup__wns" $wns_design
puts "design: $wns_design"
puts "%OL_END_REPORT"

end_metrics_file

write_sdfs
write_libs