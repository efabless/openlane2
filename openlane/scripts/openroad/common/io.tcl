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

proc read_netlist {args} {
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

proc read_libs {args} {
    sta::parse_key_args "read_libs" args \
        keys {}\
        flags {}

    set i "0"
    set tc_key "TIMING_CORNER_$i"
    puts [info exists ::env($tc_key)]
    while { [info exists ::env($tc_key)] } {
        set corner_name [lindex $::env($tc_key) 0]
        set corner_libs [lreplace $::env($tc_key) 0 0]

        set corner($corner_name) $corner_libs

        set i [expr $i + 1]
        set tc_key "TIMING_CORNER_$i"
    }

    puts $i

    if { $i != "0" } {
        # Cannot be done incrementally, believe it or not
        define_corners {*}[array name corner]

        foreach corner_name [array name corner] {
            puts "Reading libs for corner $corner_name…"
            set corner_libs $corner($corner_name)
            puts $corner_libs
            foreach lib $corner_libs {
                puts "> read_liberty -corner $corner_name $lib"
                read_liberty -corner $corner_name $lib
            }
        }

    } elseif { [get_libs -quiet *] == {} } {
        # LIB_PNR contains all libs and extra libs but with known-bad cells
        # excluded, so OpenROAD can use cells by functionality and come up
        # with a valid design.
        foreach lib $::env(LIB_PNR) {
            puts "> read_liberty $lib"
            read_liberty $lib
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

proc read_spefs {} {
    if { ![info exists ::env(CURRENT_SPEF)] } {
        return
    }

    set spef $::env(CURRENT_SPEF)
    set corners [sta::corners]
    foreach corner $corners {
        read_spef -corner [$corner name] $spef
        read_spef -corner [$corner name] $spef
        read_spef -corner [$corner name] $spef
    }

    if { [info exists ::env(EXTRA_SPEFS)] } {
        foreach {module_name spef_file_min spef_file_nom spef_file_max} "$::env(EXTRA_SPEFS)" {
            set matched 0
            foreach cell [get_cells *] {
                if { "[get_property $cell ref_name]" eq "$module_name" && !$matched } {
                    puts "Matched [get_property $cell name] with $module_name"
                    set matched 1
                    foreach corner $corners {
                        read_spef -path [get_property $cell name] -corner [$corner name] $spef_file_min
                        read_spef -path [get_property $cell name] -corner [$corner name] $spef_file_nom
                        read_spef -path [get_property $cell name] -corner [$corner name] $spef_file_max
                    }
                }
            }
            if { $matched != 1 } {
                puts "Error: Module $module_name specified in EXTRA_SPEFS not found."
                exit 1
            }
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
