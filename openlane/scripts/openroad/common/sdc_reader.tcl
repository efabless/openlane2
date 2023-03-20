proc env_var_used {var} {
    set f [open $::env(CURRENT_SDC)]
    set flag 0
    while { [gets $f line] != -1 } {
        if { [string first "\$::env($var)" $line] != -1 } {
            set flag 1
        }
    }
    close $f
    return $flag
}
set ::env(IO_PCT) [expr $::env(IO_DELAY_CONSTRAINT) / 100]
set ::env(SYNTH_TIMING_DERATE) [expr $::env(TIME_DERATING_CONSTRAINT) / 100]
set ::env(SYNTH_MAX_FANOUT) $::env(MAX_FANOUT_CONSTRAINT)
set ::env(SYNTH_CLOCK_UNCERTAINTY) $::env(CLOCK_UNCERTAINTY_CONSTRAINT)
set ::env(SYNTH_CLOCK_TRANSITION) $::env(CLOCK_TRANSITION_CONSTRAINT)

if { [env_var_used SYNTH_DRIVING_CELL_PIN] == 1 } {
    set ::env(SYNTH_DRIVING_CELL_PIN) [lindex [split $::env(SYNTH_DRIVING_CELL) "/"] 1]
    set ::env(SYNTH_DRIVING_CELL) [lindex [split $::env(SYNTH_DRIVING_CELL) "/"] 0]
}
read_sdc $::env(CURRENT_SDC)

