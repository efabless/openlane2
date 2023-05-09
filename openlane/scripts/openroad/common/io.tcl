# Copyright 2022 Efabless Corporation
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

source $::env(SCRIPTS_DIR)/openroad/common/set_global_connections.tcl

proc is_blackbox {file_path blackbox_wildcard} {
    set not_found [catch { exec bash -c "grep '$blackbox_wildcard' $file_path" }]
    return [expr !$not_found]
}

proc read_netlists {args} {
    sta::parse_key_args "read_netlists" args \
        keys {}\
        flags {-powered -all}

    set netlist $::env(CURRENT_NETLIST)
    if { [info exists flags(-powered)] } {
        set netlist $::env(CURRENT_POWERED_NETLIST)
    }

    puts "> read_verilog $netlist"
    if {[catch {read_verilog $netlist} errmsg]} {
        puts stderr $errmsg
        exit 1
    }

    if { [info exists flags(-all)] } {
        set blackbox_wildcard {/// sta-blackbox}
        if { [info exists ::env(EXTRA_VERILOG_MODELS)] } {
            foreach verilog_file $::env(EXTRA_VERILOG_MODELS) {
                if { [is_blackbox $verilog_file $blackbox_wildcard] } {
                    puts "Found '$blackbox_wildcard' in '$verilog_file', skipping…"
                } elseif { [catch {read_verilog $verilog_file} err] } {
                    puts "Error while reading $verilog_file:"
                    puts $err
                    puts "Make sure that this a gate-level netlist not an RTL file, otherwise, you can add the following comment '$blackbox_wildcard' in the file to skip it and blackbox the modules inside if needed."
                    exit 1
                }
            }
        }
    }

    link_design $::env(DESIGN_NAME)

    if { [info exists ::env(CURRENT_SDC)] } {
        if {[catch {read_sdc $::env(CURRENT_SDC)} errmsg]} {
            puts stderr $errmsg
            exit 1
        }
    }

}

proc lshift listVar {
    upvar 1 $listVar l
    set r [lindex $l 0]
    set l [lreplace $l [set l 0] 0]
    return $r
}

proc read_timing_info {args} {
    set i "0"
    set tc_key "TIMING_CORNER_$i"
    while { [info exists ::env($tc_key)] } {
        set corner_name [lindex $::env($tc_key) 0]
        set corner_libs [lreplace $::env($tc_key) 0 0]

        set corner($corner_name) $corner_libs

        set i [expr $i + 1]
        set tc_key "TIMING_CORNER_$i"
    }

    if { $i == "0" } {
        puts "\[WARN] No timing information read."
        return
    }

    define_corners {*}[array name corner]

    foreach corner_name [array name corner] {
        puts "Reading timing models for corner $corner_name…"

        set corner_models $corner($corner_name)
        foreach model $corner_models {
            if { [string match *.spef $model]} {
                puts "> read_spef -corner $corner_name $model"
                read_spef -corner $corner_name $model
            } elseif { [string match *.v $model] } {
                puts "> read_verilog $model"
                if {[catch {read_verilog $model} errmsg]} {
                    puts stderr $errmsg
                    exit 1
                }
            } else {
                puts "> read_liberty -corner $corner_name $model"
                read_liberty -corner $corner_name $model
            }
        }
        if { [info exists ::env(EXTRA_LIBS) ] } {
            puts "Reading explicitly-specified extra libs for $corner_name…"
            foreach extra_lib $::env(EXTRA_LIBS) {
                puts "> read_liberty -corner $corner_name $extra_lib"
                read_liberty -corner $corner_name $extra_lib
            }
        }
    }


    if { [file tail [info nameofexecutable]] == "sta" } {
        # OpenSTA
        read_netlists -all
        if { [info exists ::env(CURRENT_SPEF)] } {
            foreach corner_name [array name corner] {
                set spef [dict get $::env(CURRENT_SPEF) $corner_name]
                puts "> read_spef -corner $corner_name $spef"
                read_spef -corner $corner_name $spef
            }
        }
    }
}

proc read_libs {args} {
    # PNR_LIBS contains all libs and extra libs but with known-bad cells
    # excluded, so OpenROAD can use cells by functionality and come up
    # with a valid design.
    if { [get_libs -quiet *] != {} } {
        return
    }
    foreach lib $::env(PNR_LIBS) {
        puts "> read_liberty $lib"
        read_liberty $lib
    }
    if { [info exists ::env(MACRO_LIBS) ] } {
        foreach extra_lib $::env(MACRO_LIBS) {
            puts "> read_liberty $extra_lib"
            read_liberty $extra_lib
        }
    }
    if { [info exists ::env(EXTRA_LIBS) ] } {
        foreach extra_lib $::env(EXTRA_LIBS) {
            puts "> read_liberty $extra_lib"
            read_liberty $extra_lib
        }
    }
}

proc read_lefs {{tlef_key "TECH_LEF"}} {
    read_lef $::env($tlef_key)
    foreach lef $::env(CELL_LEFS) {
        read_lef $lef
    }
    if { [info exist ::env(MACRO_LEFS)] } {
        foreach lef $::env(MACRO_LEFS) {
            read_lef $lef
        }
    }
    if { [info exist ::env(EXTRA_LEFS)] } {
        foreach lef $::env(EXTRA_LEFS) {
            read_lef $lef
        }
    }
}

proc read {args} {
    sta::parse_key_args "read" args \
        keys {}\
        flags {}

    if { [info exists ::env(IO_READ_DEF)] && $::env(IO_READ_DEF) } {
        read_lefs
        if { [ catch {read_def $::env(CURRENT_DEF)} errmsg ]} {
            puts stderr $errmsg
            exit 1
        }
    } else {
        if { [ catch {read_db $::env(CURRENT_ODB)} errmsg ]} {
            puts stderr $errmsg
            exit 1
        }
    }

    read_libs

    if { [info exists ::env(CURRENT_SDC)] } {
        if {[catch {read_sdc $::env(CURRENT_SDC)} errmsg]} {
            puts stderr $errmsg
            exit 1
        }
    }
}

proc write {args} {
    # This script will attempt to write views based on existing "SAVE_"
    # environment variables. If the SAVE_ variable exists, the script will
    # attempt to write a corresponding view to the specified location.
    sta::parse_key_args "write" args \
        keys {}\
        flags {-no_global_connect}


    source $::env(SCRIPTS_DIR)/openroad/common/set_power_nets.tcl
    puts "Setting global connections for newly added cells…"
    set_global_connections

    if { [info exists ::env(SAVE_ODB)] } {
        puts "Writing OpenROAD database to '$::env(SAVE_ODB)'…"
        write_db $::env(SAVE_ODB)
    }

    if { [info exists ::env(SAVE_NETLIST)] } {
        puts "Writing netlist to '$::env(SAVE_NETLIST)'…"
        write_verilog $::env(SAVE_NETLIST)
    }

    if { [info exists ::env(SAVE_POWERED_NETLIST)] } {
        puts "Writing powered netlist to '$::env(SAVE_POWERED_NETLIST)'…"
        write_verilog -include_pwr_gnd $::env(SAVE_POWERED_NETLIST)
    }

    if { [info exists ::env(SAVE_DEF)] } {
        puts "Writing layout to '$::env(SAVE_DEF)'…"
        write_def $::env(SAVE_DEF)
    }

    if { [info exists ::env(SAVE_SDC)] } {
        puts "Writing timing constraints to '$::env(SAVE_SDC)'…"
        write_sdc -no_timestamp $::env(SAVE_SDC)
    }

    if { [info exists ::env(SAVE_SPEF)] } {
        puts "Writing extracted parasitics to '$::env(SAVE_SPEF)'…"
        write_spef $::env(SAVE_SPEF)
    }

    if { [info exists ::env(SAVE_GUIDE)] } {
        puts "Writing routing guides to '$::env(SAVE_GUIDE)'…"
        write_guides $::env(SAVE_GUIDE)
    }

    if { [info exists ::env(SAVE_SDF)] } {
        set corners [sta::corners]
        if { [llength $corners] > 1 } {
            puts "Writing SDF files for all corners…"
            set prefix [file rootname $::env(SAVE_SDF)]
            foreach corner $corners {
                set corner_name [$corner name]
                set target $prefix.$corner_name.sdf
                puts "Writing SDF for the $corner_name corner to $target…"
                write_sdf -include_typ -divider . -corner $corner_name $target
            }
        } else {
            puts "Writing SDF to '$::env(SAVE_SDF)'…"
            write_sdf -include_typ -divider . $::env(SAVE_SDF)
        }
    }
}

proc write_libs {} {
    if { [info exists ::env(LIB_SAVE_PATH)] && (![info exists ::(STA_PRE_CTS)] || !$::env(STA_PRE_CTS))} {
        set corners [sta::corners]
        puts "Writing timing models for all corners…"
        foreach corner $corners {
            set corner_name [$corner name]
            set target $::env(LIB_SAVE_PATH)/$corner_name.lib
            puts "Writing timing models for the $corner_name corner to $target…"
            write_timing_model -corner $corner_name $target
        }
    }
}
