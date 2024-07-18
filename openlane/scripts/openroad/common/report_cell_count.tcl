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
    set decap_count 0
    set diode_count 0
    set cts_count 0
    set diode_pattern [lindex [split "$::env(DIODE_CELL)" "/"] 0]

    foreach inst [$block getInsts] {
        set master [$inst getMaster]
        if { [search_multi_pattern "[$master getName]" "$::env(DECAP_CELL)"] } {
            set decap_count [expr $decap_count + 1]
        }
        if { [search_multi_pattern "[$master getName]" "$::env(FILL_CELL)"] } {
            set fill_count [expr $fill_count + 1]
        }
        if { [search_multi_pattern "[$master getName]" "$::env(WELLTAP_CELL)"] } {
            set tap_count [expr $tap_count + 1]
        }
        if { [search_multi_pattern "[$master getName]" "$::env(CTS_CLK_BUFFERS) $::env(CTS_ROOT_BUFFER)"] } {
            set cts_count [expr $cts_count + 1]
        }
        if { [search_multi_pattern "[$master getName]" "$diode_pattern"] } {
            set diode_count [expr $diode_count + 1]
        }
        set cell_count_total [expr $cell_count_total + 1]
    }

    write_metric_int "design__instance__count__total" $cell_count_total
    write_metric_int "design__instance__count__welltap" $tap_count
    write_metric_int "design__instance__count__diode" $diode_count
    write_metric_int "design__instance__count__fill" $fill_count
    write_metric_int "design__instance__count__cts" $cts_count
    write_metric_int "design__instance__count__decap" $decap_count
}

