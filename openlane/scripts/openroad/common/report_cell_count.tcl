source $::env(SCRIPTS_DIR)/openroad/common/io.tcl

proc search_multi_pattern {name patterns} {
    foreach pattern $patterns {
        if { [lsearch -glob $name $pattern] != -1 } {
            return true
        }
    }
    return false
}

proc report_cell_count {args} {
    set db [::ord::get_db]
    set block [[$db getChip] getBlock]
    set cell_count_total 0
    set fill_count 0
    set tap_count 0
    set diode_count 0
    set cts_count 0
    set buffer_count 0
    set inverter_count 0
    set memory_cell_count 0
    set clock_gate_count 0
    set diode_pattern [lindex [split "$::env(DIODE_CELL)" "/"] 0]

    foreach inst [$block getInsts] {
        set opensta_instance [get_cells [$inst getName]] ;# exposes different apis
        set types [split [[$inst getMaster] getType] _]
        if { "CORE" in $types && "SPACER" in $types } {
            set fill_count [expr $fill_count + 1]
        }
        if { "CORE" in $types && "WELLTAP" in $types } {
            set tap_count [expr $tap_count + 1]
        }
        if { "CORE" in $types && "ANTENNACELL" in $types } {
            set diode_count [expr $diode_count + 1]
        }
        if { [get_property $opensta_instance is_buffer] } {
            set buffer_count [expr $buffer_count + 1]
        }
        if { [get_property $opensta_instance is_inverter] } {
            set inverter_count [expr $inverter_count + 1]
        }
        if { [get_property $opensta_instance is_memory_cell] } {
            set memory_cell_count [expr $memory_cell_count + 1]
        }
        if { [get_property $opensta_instance is_clock_gate] } {
            set clock_gate_count [expr $clock_gate_count + 1]
        }
        set cell_count_total [expr $cell_count_total + 1]
    }

    write_metric_int "design__instance__count__total" $cell_count_total
    write_metric_int "design__instance__count__welltap" $tap_count
    write_metric_int "design__instance__count__diode" $diode_count
    write_metric_int "design__instance__count__fill" $fill_count
    write_metric_int "design__instance__count__buffer" $buffer_count
    write_metric_int "design__instance__count__inverter" $inverter_count
    write_metric_int "design__instance__count__memory_cell" $memory_cell_count
    write_metric_int "design__instance__count__clock_gate" $clock_gate_count
}
