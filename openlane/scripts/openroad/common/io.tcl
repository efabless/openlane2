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

proc string_in_file {file_path substring} {
    set f [open $file_path r]
    set data [read $f]
    close $f

    if { [string first $substring $data] != -1} {
        return 1
    }
    return 0
}

proc env_var_used {file var} {
    return [string_in_file $file "\$::env($var)"]
}

proc read_current_sdc {} {
    if { ![info exists ::env(CURRENT_SDC)]} {
        puts "\[INFO] CURRENT_SDC not found. Not reading an SDC file."
        return
    }
    set ::env(IO_PCT) [expr $::env(IO_DELAY_CONSTRAINT) / 100]
    set ::env(SYNTH_TIMING_DERATE) [expr $::env(TIME_DERATING_CONSTRAINT) / 100]
    set ::env(SYNTH_MAX_FANOUT) $::env(MAX_FANOUT_CONSTRAINT)
    set ::env(SYNTH_CLOCK_UNCERTAINTY) $::env(CLOCK_UNCERTAINTY_CONSTRAINT)
    set ::env(SYNTH_CLOCK_TRANSITION) $::env(CLOCK_TRANSITION_CONSTRAINT)
    if { [info exists ::env(MAX_TRANSITION_CONSTRAINT)] } {
        set ::env(SYNTH_MAX_TRAN) $::env(MAX_TRANSITION_CONSTRAINT)
    }

    if { [env_var_used $::env(CURRENT_SDC) SYNTH_DRIVING_CELL_PIN] == 1 } {
        set ::env(SYNTH_DRIVING_CELL_PIN) [lindex [split $::env(SYNTH_DRIVING_CELL) "/"] 1]
        set ::env(SYNTH_DRIVING_CELL) [lindex [split $::env(SYNTH_DRIVING_CELL) "/"] 0]
    }

    puts "Reading design constraints file at '$::env(CURRENT_SDC)'…"
    if {[catch {read_sdc $::env(CURRENT_SDC)} errmsg]} {
        puts stderr $errmsg
        exit 1
    }
}


proc read_current_netlist {args} {
    sta::parse_key_args "read_current_netlist" args \
        keys {}\
        flags {-powered -all}

    puts "Reading top-level netlist at '$::env(CURRENT_NETLIST)'…"
    if {[catch {read_verilog $::env(CURRENT_NETLIST)} errmsg]} {
        puts stderr $errmsg
        exit 1
    }

    puts "Linking design '$::env(DESIGN_NAME)' from netlist…"
    link_design $::env(DESIGN_NAME)

    read_current_sdc

}

proc read_timing_info {args} {
    if { ![info exists ::env(CURRENT_CORNER_NAME)] } {
        return
    }
    set corner_name $::env(CURRENT_CORNER_NAME)
    define_corners $corner_name

    puts "Reading timing models for corner $corner_name…"

    set macro_spefs [list]
    set macro_nls [list]
    set corner_models $::env(CURRENT_CORNER_TIMING_VIEWS)
    foreach model $corner_models {
        if { [string match *.spef $model]} {
            lappend macro_spefs $corner_name $model
        } elseif { [string match *.v $model] } {
            lappend macro_nls $model
        } else {
            puts "Reading timing library for the '$corner_name' corner at '$model'…"
            read_liberty -corner $corner_name $model
        }
    }

    if { [info exists ::env(EXTRA_LIBS) ] } {
        puts "Reading explicitly-specified extra libs for $corner_name…"
        foreach extra_lib $::env(EXTRA_LIBS) {
            puts "Reading extra timing library for the '$corner_name' corner at '$extra_lib'…"
            read_liberty -corner $corner_name $extra_lib
        }
    }

    set blackbox_wildcard {/// sta-blackbox}
    foreach nl $macro_nls {
        puts "Reading macro netlist at '$nl'…"
        if { [catch {read_verilog $nl} err] } {
            puts "Error while reading macro netlist '$nl':"
            puts $err
            puts "Make sure that this a gate-level netlist and not an RTL file."
            exit 1
        }
    }
    if { [info exists ::env(EXTRA_VERILOG_MODELS)] } {
        foreach verilog_file $::env(EXTRA_VERILOG_MODELS) {
            if { [string_in_file $verilog_file $blackbox_wildcard] } {
                puts "Found '$blackbox_wildcard' in '$verilog_file', skipping…"
            } elseif { [catch {puts "Reading Verilog model at '$verilog_file'…"; read_verilog $verilog_file} err] } {
                puts "Error while reading $verilog_file:"
                puts $err
                puts "Make sure that this a gate-level netlist and not an RTL file, otherwise, you can add the following comment '$blackbox_wildcard' in the file to skip it and blackbox the modules inside if needed."
                exit 1
            }
        }
    }
    read_current_netlist
    set ::macro_spefs $macro_spefs
}

proc read_spefs {} {
    if { [info exists ::env(CURRENT_SPEF_BY_CORNER)] } {
        foreach {corner_name spef} $::env(CURRENT_SPEF_BY_CORNER) {
            puts "Reading top-level design parasitics for the '$corner_name' corner at '$spef'…"
            read_spef -corner $corner_name $spef
        }
    }
    if { [info exists ::macro_spefs] } {
        foreach {corner_name spef_info} $::macro_spefs {
            set fields [split $spef_info "@"]
            lassign $fields instance_path spef
            puts "Reading '$instance_path' parasitics for the '$corner_name' corner at '$spef'…"
            read_spef -corner $corner_name -path $instance_path $spef
        }
    }
}

proc read_pnr_libs {args} {
    # PNR_LIBS contains all libs and extra libs but with known-bad cells
    # excluded, so OpenROAD can use cells by functionality and come up
    # with a valid design.

    # If there are ANY libs already read- just leave
    if { [get_libs -quiet *] != {} } {
        return
    }

    define_corners $::env(DEFAULT_CORNER)

    foreach lib $::env(PNR_LIBS) {
        puts "Reading library file at '$lib'…"
        read_liberty $lib
    }
    if { [info exists ::env(MACRO_LIBS) ] } {
        foreach macro_lib $::env(MACRO_LIBS) {
            puts "Reading macro library file at '$macro_lib'…"
            read_liberty $macro_lib
        }
    }
    if { [info exists ::env(EXTRA_LIBS) ] } {
        foreach extra_lib $::env(EXTRA_LIBS) {
            puts "Reading extra library file at '$extra_lib'…"
            read_liberty $extra_lib
        }
    }
}

proc read_lefs {{tlef_key "TECH_LEF"}} {
    set tlef $::env($tlef_key)

    puts "Reading technology LEF file at '$tlef'…"
    read_lef $tlef

    foreach lef $::env(CELL_LEFS) {
        puts "Reading cell LEF file at '$lef'…"
        read_lef $lef
    }
    if { [info exist ::env(MACRO_LEFS)] } {
        foreach lef $::env(MACRO_LEFS) {
            puts "Reading macro LEF file at '$lef'…"
            read_lef $lef
        }
    }
    if { [info exist ::env(EXTRA_LEFS)] } {
        foreach lef $::env(EXTRA_LEFS) {
            puts "Reading extra LEF file at '$lef'…"
            read_lef $lef
        }
    }
}

proc read_current_odb {args} {
    sta::parse_key_args "read_current_odb" args \
        keys {}\
        flags {}

    puts "Reading OpenROAD database at '$::env(CURRENT_ODB)'…"
    if { [ catch {read_db $::env(CURRENT_ODB)} errmsg ]} {
        puts stderr $errmsg
        exit 1
    }

    # Read supporting views (if applicable)
    read_pnr_libs
    read_current_sdc
}

proc write_views {args} {
    # This script will attempt to write views based on existing "SAVE_"
    # environment variables. If the SAVE_ variable exists, the script will
    # attempt to write a corresponding view to the specified location.
    sta::parse_key_args "write_views" args \
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
        } else {
            puts "Writing SDF to '$::env(SAVE_SDF)'…"
            write_sdf -include_typ -divider . $::env(SAVE_SDF)
        }
    }
}

proc write_sdfs {} {
    if { [info exists ::env(SDF_SAVE_DIR)] } {
        set corners [sta::corners]

        puts "Writing SDF files for all corners…"
        foreach corner $corners {
            set corner_name [$corner name]
            set target $::env(SDF_SAVE_DIR)/$::env(DESIGN_NAME)__$corner_name.sdf
            write_sdf -include_typ -divider . -corner $corner_name $target
        }
    }
}

proc write_libs {} {
    if { [info exists ::env(LIB_SAVE_DIR)] && (![info exists ::(STA_PRE_CTS)] || !$::env(STA_PRE_CTS))} {
        set corners [sta::corners]
        puts "Writing timing models for all corners…"
        foreach corner $corners {
            set corner_name [$corner name]
            set target $::env(LIB_SAVE_DIR)/$::env(DESIGN_NAME)__$corner_name.lib
            puts "Writing timing models for the $corner_name corner to $target…"
            write_timing_model -corner $corner_name $target
        }
    }
}

proc max {a b} {
    if { $a > $b } {
        return $a
    } else {
        return $b
    }
}

set ::metric_count 0
set ::metrics_file ""
if { [info exists ::env(OPENSTA)] && $::env(OPENSTA) } {
    proc write_metric_num {metric value} {
        if { $value == 1e30 } {
            write_metric_str $metric Infinity
        } elseif { $value == -1e30 } {
            write_metric_str $metric -Infinity
        } else {
            puts "%OL_METRIC_F $metric $value"
        }
    }
    proc write_metric_int {metric value} {
        puts "%OL_METRIC_I $metric $value"
    }
    proc write_metric_str {metric value} {
        puts "%OL_METRIC $metric $value"
    }
} else {
    proc write_metric_str {metric value} {
        puts "Writing metric $metric: $value"
        utl::metric $metric $value
    }
    proc write_metric_int {metric value} {
        puts "Writing metric $metric: $value"
        utl::metric_int $metric $value
    }
    proc write_metric_num {metric value} {
        puts "Writing metric $metric: $value"
        utl::metric_float $metric $value
    }
}