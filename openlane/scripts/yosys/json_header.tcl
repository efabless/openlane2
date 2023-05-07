yosys -import
set vIdirsArgs ""
set vtop $::env(DESIGN_NAME)
if {[info exist ::env(VERILOG_INCLUDE_DIRS)]} {
    foreach dir $::env(VERILOG_INCLUDE_DIRS) {
        lappend vIdirsArgs "-I$dir"
    }
    set vIdirsArgs [join $vIdirsArgs]
}
if { [info exists ::env(SYNTH_DEFINES) ] } {
    foreach define $::env(SYNTH_DEFINES) {
        log "Defining $define"
        verilog_defines -D$define
    }
}
if { [info exists ::env(SYNTH_POWER_DEFINE)] } {
    verilog_defines -D$::env(SYNTH_POWER_DEFINE)
}
if { $::env(SYNTH_READ_BLACKBOX_LIB) } {
    log "Reading $::env(LIB) as a blackbox"
    foreach lib $::env(LIB) {
        read_liberty -lib -ignore_miss_dir -setattr blackbox $lib
    }
}
if { [info exists ::env(EXTRA_LIBS) ] } {
    foreach lib $::env(EXTRA_LIBS) {
        read_liberty -lib -ignore_miss_dir -setattr blackbox $lib
    }
}
if { [info exists ::env(EXTRA_VERILOG_MODELS)] } {
    foreach verilog_file $::env(EXTRA_VERILOG_MODELS) {
        read_verilog -sv -lib {*}$vIdirsArgs $verilog_file
    }
}
for { set i 0 } { $i < [llength $::env(VERILOG_FILES)] } { incr i } {
    read_verilog -sv {*}$vIdirsArgs [lindex $::env(VERILOG_FILES) $i]
}
select -module $vtop
yosys proc
json -o $::env(SAVE_JSON_HEADER)
