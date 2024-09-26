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
    set diode_pattern [lindex [split "$::env(DIODE_CELL)" "/"] 0]
    set physical_welltap 0
    set physical_spacer 0
    set physical_antennacell 0
    set physical_misc 0
    set inverter 0
    set sequential 0
    set buffer 0
    set clock_gate 0
    set logical 0
    set macros 0
    set insts [$::block getInsts]
    foreach inst $insts {
        set opensta_instance [get_cells [$inst getName]] ;# exposes different apis
        set lef_master [$inst getMaster]
        set types [split [$lef_master getType] _]
        if { "$types" == "CORE" } {
            if { [get_property $opensta_instance is_buffer] } {
                incr buffer
            } elseif { [$lef_master isSequential] } {
                incr sequential
            } elseif { [get_property $opensta_instance is_clock_gate] } {
                incr clock_gate
            } else {
                incr logical
            }
        } elseif { "$types" == "BLOCK" } {
            incr macros
        } else {
            if { "SPACER" in $types } {
                incr physical_spacer
            } elseif { "WELLTAP" in $types } {
                incr physical_welltap
            } elseif { "ANTENNACELL" in $types } {
                incr physical_antennacell
            } else {
                incr physical_misc
            }
        }
    }

    write_metric_int "design__instance__count" [llength $insts]
    write_metric_int "design__instance__count__macros" $macros
    write_metric_int "design__instance__count__stdcell__type:physical__class:welltap" $physical_welltap
    write_metric_int "design__instance__count__stdcell__type:physical__class:antennacell" $physical_antennacell
    write_metric_int "design__instance__count__stdcell__type:physical__class:spacer" $physical_spacer
    write_metric_int "design__instance__count__stdcell__type:physical__class:misc" $physical_misc
    write_metric_int "design__instance__count__stdcell__type:logical__class:sequential" $sequential
    write_metric_int "design__instance__count__stdcell__type:logical__class:buffer" $buffer
    write_metric_int "design__instance__count__stdcell__type:logical__class:clock_gate" $clock_gate
    write_metric_int "design__instance__count__stdcell__type:logical__class:misc" $logical
}
