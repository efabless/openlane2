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

# This file supports one defined corner per-process.
# Any more defined corners will be ignored.
# Aggregation is left to the OpenLane step.


source $::env(SCRIPTS_DIR)/openroad/common/io.tcl

set_cmd_units\
    -time ns\
    -capacitance pF\
    -current mA\
    -voltage V\
    -resistance kOhm\
    -distance um

set sta_report_default_digits 6

if { ![info exists ::env(OPENSTA)] || !$::env(OPENSTA) } {
    read_current_odb

    # Internal API- brittle
    if { [grt::have_routes] } {
        estimate_parasitics -global_routing
    } elseif { [rsz::check_corner_wire_cap] } {
        estimate_parasitics -placement
    }
} else {
    read_timing_info
}
read_spefs

set_propagated_clock [all_clocks]

set corner [lindex [sta::corners] 0]
sta::set_cmd_corner $corner

set clocks [sta::sort_by_name [sta::all_clocks]]

puts "%OL_CREATE_REPORT min.rpt"
puts "\n==========================================================================="
puts "report_checks -path_delay min (Hold)"
puts "============================================================================"
puts "======================= [$corner name] Corner ===================================\n"
report_checks -sort_by_slack -path_delay min -fields {slew cap input nets fanout} -format full_clock_expanded -group_count 1000 -corner [$corner name]
puts ""
puts "%OL_END_REPORT"


puts "%OL_CREATE_REPORT max.rpt"
puts "\n==========================================================================="
puts "report_checks -path_delay max (Setup)"
puts "============================================================================"
puts "======================= [$corner name] Corner ===================================\n"
report_checks -sort_by_slack -path_delay max -fields {slew cap input nets fanout} -format full_clock_expanded -group_count 1000 -corner [$corner name]
puts ""
puts "%OL_END_REPORT"


puts "%OL_CREATE_REPORT checks.rpt"
puts "\n==========================================================================="
puts "report_checks -unconstrained"
puts "==========================================================================="
puts "======================= [$corner name] Corner ===================================\n"
report_checks -unconstrained -fields {slew cap input nets fanout} -format full_clock_expanded -corner [$corner name]
puts ""


puts "\n==========================================================================="
puts "report_checks --slack_max -0.01"
puts "============================================================================"
puts "======================= [$corner name] Corner ===================================\n"
report_checks -slack_max -0.01 -fields {slew cap input nets fanout} -format full_clock_expanded -corner [$corner name]
puts ""

puts "\n==========================================================================="
puts " report_check_types -max_slew -max_cap -max_fanout -violators"
puts "============================================================================"
puts "======================= [$corner name] Corner ===================================\n"
report_check_types -max_slew -max_capacitance -max_fanout -violators -corner [$corner name]
puts ""

puts "\n==========================================================================="
puts "report_parasitic_annotation -report_unannotated"
puts "============================================================================"
report_parasitic_annotation -report_unannotated

puts "\n==========================================================================="
puts "max slew violation count [sta::max_slew_violation_count]"
write_metric_int "clock__max_slew_violation__count__corner:[$corner name]" [sta::max_slew_violation_count]
puts "max fanout violation count [sta::max_fanout_violation_count]"
write_metric_int "design__max_fanout_violation__count__corner:[$corner name]" [sta::max_fanout_violation_count]
puts "max cap violation count [sta::max_capacitance_violation_count]"
write_metric_int "design__max_cap_violation__count__corner:[$corner name]" [sta::max_capacitance_violation_count]
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
puts "======================= [$corner name] Corner ===================================\n"
report_power -corner [$corner name]
puts ""
puts "%OL_END_REPORT"


puts "%OL_CREATE_REPORT skew.min.rpt"
puts "\n==========================================================================="
puts "Clock Skew (Hold)"
puts "============================================================================"
set skew_corner [sta::format_time [sta::worst_clk_skew_cmd "min"] $sta_report_default_digits]
write_metric_num "clock__skew__worst_hold__corner:[$corner name]" $skew_corner

puts "======================= [$corner name] Corner ===================================\n"
report_clock_skew -corner [$corner name] -hold

puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT skew.max.rpt"
puts "\n==========================================================================="
puts "Clock Skew (Setup)"
puts "============================================================================"
set skew_corner [sta::format_time [sta::worst_clk_skew_cmd "max"] $sta_report_default_digits]

write_metric_num "clock__skew__worst_setup__corner:[$corner name]" $skew_corner

puts "======================= [$corner name] Corner ===================================\n"
report_clock_skew -corner [$corner name] -setup

puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT ws.min.rpt"
puts "\n==========================================================================="
puts "Worst Slack (Hold)"
puts "============================================================================"
set ws [sta::format_time [sta::worst_slack_corner $corner "min"] $sta_report_default_digits]
write_metric_num "timing__hold__ws__corner:[$corner name]" $ws
puts "[$corner name]: $ws"
puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT ws.max.rpt"
puts "\n==========================================================================="
puts "Worst Slack (Setup)"
puts "============================================================================"

set ws [sta::format_time [sta::worst_slack_corner $corner "max"] $sta_report_default_digits]
write_metric_num "timing__setup__ws__corner:[$corner name]" $ws
puts "[$corner name]: $ws"
puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT tns.min.rpt"
puts "\n==========================================================================="
puts "Total Negative Slack (Hold)"
puts "============================================================================"

set tns [sta::format_time [sta::total_negative_slack_corner_cmd $corner "min"] $sta_report_default_digits]
write_metric_num "timing__hold__tns__corner:[$corner name]" $tns
puts "[$corner name]: $tns"
puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT tns.max.rpt"
puts "\n==========================================================================="
puts "Total Negative Slack (Setup)"
puts "============================================================================"
set tns_design 0
foreach corner [sta::corners] {
    set tns [sta::format_time [sta::total_negative_slack_corner_cmd $corner "max"] $sta_report_default_digits]
    write_metric_num "timing__setup__tns__corner:[$corner name]" $tns
    puts "[$corner name]: $tns"
}
puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT wns.min.rpt"
puts "\n==========================================================================="
puts "Worst Negative Slack (Hold)"
puts "============================================================================"

set ws [sta::format_time [sta::worst_slack_corner $corner "min"] $sta_report_default_digits]
set wns 0
if { $ws < 0 } {
    set wns $ws
}
write_metric_num "timing__hold__wns__corner:[$corner name]" $wns
puts "[$corner name]: $wns"
puts "%OL_END_REPORT"

puts "%OL_CREATE_REPORT wns.max.rpt"
puts "\n==========================================================================="
puts "Worst Negative Slack (Setup)"
puts "============================================================================"

set ws [sta::format_time [sta::worst_slack_corner $corner "max"] $sta_report_default_digits]
set wns 0.0
if { $ws < 0 } {
    set wns $ws
}
write_metric_num "timing__setup__wns__corner:[$corner name]" $wns
puts "[$corner name]: $wns"
puts "%OL_END_REPORT"

proc check_if_terminal {pin_object} {
    set net [get_nets -of_object $pin_object]
    if { "$net" == "NULL" } {
        return 1
    }
    return 0
}

puts "%OL_CREATE_REPORT violator_list.rpt"
puts "\n==========================================================================="
puts "Violator List"
puts "============================================================================"

set total_hold_vios 0
set r2r_hold_vios 0
set total_setup_vios 0
set r2r_setup_vios 0

set hold_timing_paths [find_timing_paths -unique_paths_to_endpoint -path_delay min -sort_by_slack -group_count 999999999 -slack_max 0]
foreach path $hold_timing_paths {
    set from "reg"
    set to "reg"

    set start_pin [get_property $path startpoint]
    set end_pin [get_property $path endpoint]

    if { [check_if_terminal $start_pin] } {
        set from "in"
    }
    if { [check_if_terminal $end_pin] } {
        set to "out"
    }
    set kind "$from-$to"

    incr total_hold_vios
    if { "$kind" == "reg-reg" } {
        incr r2r_hold_vios
    }

    puts "\[hold $kind] [get_property $start_pin full_name] -> [get_property $end_pin full_name] : [get_property $path slack]"
}

set setup_timing_paths [find_timing_paths -unique_paths_to_endpoint -path_delay max -sort_by_slack -group_count 999999999 -slack_max 0]
foreach path $setup_timing_paths {
    set from "reg"
    set to "reg"

    set start_pin [get_property $path startpoint]
    set end_pin [get_property $path endpoint]

    if { [check_if_terminal $start_pin] } {
        set from "in"
    }
    if { [check_if_terminal $end_pin] } {
        set to "out"
    }

    set kind "$from-$to"

    incr total_setup_vios
    if { "$kind" == "reg-reg" } {
        incr r2r_setup_vios
    }

    puts "\[setup $kind] [get_property $start_pin full_name] -> [get_property $end_pin full_name] : [get_property $path slack]"
}

write_metric_int "timing__hold_vio__count__corner:[$corner name]" $total_hold_vios
write_metric_int "timing__hold_r2r_vio__count__corner:[$corner name]" $r2r_hold_vios
write_metric_int "timing__setup_vio__count__corner:[$corner name]" $total_setup_vios
write_metric_int "timing__setup_r2r_vio__count__corner:[$corner name]" $r2r_setup_vios
puts "%OL_END_REPORT"


write_sdfs
write_libs