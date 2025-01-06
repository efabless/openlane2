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
#
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


set i "0"
set tc_key "_LAYER_RC_$i"

while { [info exists ::env($tc_key)] } {
    # [$corner] + [layer] + [str(round(res, 8))] + [str(round(cap, 8))]
    set corner_name [lindex $::env($tc_key) 0]
    set layer_name [lindex $::env($tc_key) 1]
    set res_value [lindex $::env($tc_key) 2]
    set cap_value [lindex $::env($tc_key) 3]
    puts "\[INFO\] Setting $layer_name $corner_name to res $res_value and cap $cap_value"
    set_layer_rc \
        -layer $layer_name\
        -capacitance $cap_value\
        -corner $corner_name\
        -resistance $res_value
    incr i
    set tc_key "_LAYER_RC_$i"
}


set i "0"
set tc_key "_VIA_RC_$i"

while { [info exists ::env($tc_key)] } {
    set corner_name [lindex $::env($tc_key) 0]
    set via_name [lindex $::env($tc_key) 1]
    set res_value [lindex $::env($tc_key) 2]
    puts "\[INFO\] Setting $via_name $corner_name to res $res_value"
    set_layer_rc \
        -via $via_name\
        -resistance $res_value\
        -corner $corner_name
    incr i
    set tc_key "_VIA_RC_$i"
}

set layer_names [get_routing_layer_names]
set signal_wire_rc_layers $layer_names
set clock_wire_rc_layers $layer_names
if { [info exist ::env(SIGNAL_WIRE_RC_LAYERS)] } {
    set signal_wire_rc_layers $::env(SIGNAL_WIRE_RC_LAYERS)
}
if { [info exist ::env(CLOCK_WIRE_RC_LAYERS)] } {
    set clock_wire_rc_layers $::env(CLOCK_WIRE_RC_LAYERS)
}
if { [llength $signal_wire_rc_layers] > 1 } {
    set_wire_rc -signal -layers "$signal_wire_rc_layers"
} else {
    set_wire_rc -signal -layer "$signal_wire_rc_layers"
}
if { [llength $clock_wire_rc_layers] > 1 } {
    set_wire_rc -clock -layers "$clock_wire_rc_layers"
} else {
    set_wire_rc -clock -layer "$clock_wire_rc_layers"
}

# keeping this until there is a clear resolution for https://github.com/The-OpenROAD-Project/OpenROAD/issues/6175
#if { ![info exists ::env($tc_key)] } {
#    puts "\[INFO\] Using default RC values from the technology for metal layers"
#    set res_unit [sta::unit_scale resistance] 
#    set cap_unit [sta::unit_scale capacitance]
#
#    foreach layer [$::tech getLayers] {
#        if { [$layer getType] == "ROUTING" } {
#            set layer_name [$layer getName]
#
#            lassign [rsz::dblayer_wire_rc $layer] layer_wire_res_ohm_m layer_wire_cap_farad_m
#            set layer_wire_res_unit_microns [expr $layer_wire_res_ohm_m * 1e-6 / $res_unit]
#            set layer_wire_cap_unit_microns [expr $layer_wire_cap_farad_m * 1e-6 / $cap_unit]
#
#            foreach corner [sta::corners] {
#                set_layer_rc \
#                    -layer $layer_name\
#                    -capacitance $layer_wire_cap_unit_microns\
#                    -corner [$corner name]\
#                    -resistance $layer_wire_res_unit_microns
#            }
#        }
#    }
#}
#
#if { ![info exists ::env($tc_key)] } {
#    puts "\[INFO\] Using default RC values from the technology for vias"
#
#    foreach layer [$::tech getLayers] {
#        if { [$layer getType] == "CUT" } {
#            set layer_name [$layer getName]
#            set res [$layer getResistance]
#            foreach corner [sta::corners] {
#                set_layer_rc \
#                    -corner [$corner name]\
#                    -resistance $res\
#                    -via $layer_name
#            }
#        }
#    }
#}
