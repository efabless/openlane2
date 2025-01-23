# Copyright 2021-2022 Efabless Corporation
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

# Resistance/Capacitance Overrides
# Via resistance

proc get_routing_layer_names {} {
    set layer_names [list]
    set layers [$::tech getLayers]
    set adding 0
    foreach layer $layers {
        if { [$layer getRoutingLevel] >= 1 } {
            set name [$layer getName]
            if {"$::env(RT_MIN_LAYER)" == "$name"} {
                set adding 1
            }
            if { $adding } {
                lappend layer_names $name
            }

            if {"$::env(RT_MAX_LAYER)" == "$name"} {
                set adding 0
            }
        }
    }
    return $layer_names
}

proc set_layers_custom_rc {args} {
    set i "0"
    set tc_key "_LAYER_RC_$i"
    set custom_corner_rc [list]
    while { [info exists ::env($tc_key)] } {
        # [$corner] + [layer] + [str(round(res, 8))] + [str(round(cap, 8))]
        set corner_name [lindex $::env($tc_key) 0]
        set layer_name [lindex $::env($tc_key) 1]
        set res_value [lindex $::env($tc_key) 2]
        set cap_value [lindex $::env($tc_key) 3]
        log_cmd set_layer_rc \
            -layer $layer_name\
            -capacitance $cap_value\
            -corner $corner_name\
            -resistance $res_value
        incr i
        set tc_key "_LAYER_RC_$i"
        if { [lsearch $custom_corner_rc $corner_name] == -1 } {
            lappend custom_corner_rc $corner_name
        }
    }
    return $custom_corner_rc
}

proc set_via_custom_r {args} {
    set i "0"
    set tc_key "_VIA_R_$i"
    set custom_corner_r [list]
    while { [info exists ::env($tc_key)] } {
        set corner_name [lindex $::env($tc_key) 0]
        set via_name [lindex $::env($tc_key) 1]
        set res_value [lindex $::env($tc_key) 2]
        log_cmd set_layer_rc \
            -via $via_name\
            -resistance $res_value\
            -corner $corner_name
        incr i
        set tc_key "_VIA_R_$i"

        if { [lsearch $custom_corner_r $corner_name] == -1 } {
            lappend custom_corner_r $corner_name
        }
    }
    return $custom_corner_r
}


proc get_missing_corners {corners_with_custom_layer_rc} {
    set corners [sta::corners]
    set corners_without_custom_layer_rc [list]
    foreach corner $corners {
        if {[string first [$corner name] "$corners_with_custom_layer_rc"] == -1} {
            lappend corners_without_custom_layer_rc [$corner name]
        }
    }
    return $corners_without_custom_layer_rc
}

proc set_layers_default_rc {corners} {
    set res_unit [sta::unit_scale resistance] 
    set cap_unit [sta::unit_scale capacitance]
    foreach layer [$::tech getLayers] {
        if { [$layer getType] == "ROUTING" } {
            set layer_name [$layer getName]
            lassign [rsz::dblayer_wire_rc $layer] layer_wire_res_ohm_m layer_wire_cap_farad_m
            set layer_wire_res_unit_microns [expr $layer_wire_res_ohm_m * 1e-6 / $res_unit]
            set layer_wire_cap_unit_microns [expr $layer_wire_cap_farad_m * 1e-6 / $cap_unit]
            foreach corner "$corners" {
                log_cmd set_layer_rc \
                    -layer $layer_name\
                    -capacitance $layer_wire_cap_unit_microns\
                    -corner $corner\
                    -resistance $layer_wire_res_unit_microns
            }
        }
    }
}

proc set_vias_default_r {corners} {
    foreach layer [$::tech getLayers] {
        if { [$layer getType] == "CUT" } {
            set layer_name [$layer getName]
            set res [$layer getResistance]
            foreach corner $corners {
                log_cmd set_layer_rc \
                    -corner $corner\
                    -resistance $res\
                    -via $layer_name
            }
        }
    }
}

proc set_wire_rc_wrapper {use_corners} {
    set layer_names [get_routing_layer_names]
    set signal_wire_rc_layers $layer_names
    set clock_wire_rc_layers $layer_names
    if { [info exist ::env(SIGNAL_WIRE_RC_LAYERS)] } {
        set signal_wire_rc_layers $::env(SIGNAL_WIRE_RC_LAYERS)
    }
    if { [info exist ::env(CLOCK_WIRE_RC_LAYERS)] } {
        set clock_wire_rc_layers $::env(CLOCK_WIRE_RC_LAYERS)
    }
    set signal_args [list]
    lappend signal_args -signal
    if { [llength $signal_wire_rc_layers] > 1 } {
        lappend signal_args -layers "$signal_wire_rc_layers"
    } else {
        lappend signal_args -layer "$signal_wire_rc_layers"
    }

    set clock_args [list]
    lappend clock_args -clock
    if { [llength $clock_wire_rc_layers] > 1 } {
        lappend clock_args -layers "$clock_wire_rc_layers"
    } else {
        lappend clock_args -layer "$clock_wire_rc_layers"
    }

    if { $use_corners } {
        foreach corner [sta::corners] {
            log_cmd set_wire_rc {*}$clock_args -corner [$corner name]
            log_cmd set_wire_rc {*}$signal_args -corner [$corner name]
        }
    } else {
            log_cmd set_wire_rc {*}$clock_args
            log_cmd set_wire_rc {*}$signal_args
    }
}

# Flow as follows
# 1. Set layers custom rc - if defined
# 2. Set vias custom r - if defined
# 3. If (1) doesn't override all the corners, set the default techlef value for the remaining corners for layers
# 3.a If (2) doesn't override all the corners, set the default techlef value for the remaining corners for vias
# 4. If (1) doesn't override the corners at all, call set_wire_rc without -corner, to ensure the default behavior
# 5. If (1) does override (some) corners, we must use set_wire_rc with -corner, becuase otherwise set_wire_rc will set the default techlef value for all existing corners

set corners_with_custom_layer_rc [set_layers_custom_rc]
set corners_with_custom_via_r [set_via_custom_r]
set corners_without_custom_layer_rc [get_missing_corners $corners_with_custom_layer_rc]
set corners_witout_custom_via_r [get_missing_corners $corners_with_custom_via_r]

if { [llength $corners_with_custom_layer_rc] } {
    # to avoid setting the default values again for round off error and maintain old behavior
    log_cmd set_layers_default_rc $corners_without_custom_layer_rc
}
if { [llength $corners_with_custom_via_r] } {
    log_cmd set_vias_default_r $corners_witout_custom_via_r
}
if { [llength $corners_with_custom_layer_rc] } {
    log_cmd set_wire_rc_wrapper 1
} else {
    log_cmd set_wire_rc_wrapper 0
}
