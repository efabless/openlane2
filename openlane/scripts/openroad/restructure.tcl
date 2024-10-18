source $::env(SCRIPTS_DIR)/openroad/common/io.tcl

read_current_odb

if { $::env(RMP_TARGET) == "timing" } {
    repair_design
    repair_timing
}
set arg_list [list]
lappend arg_list -tiehi_port $::env(SYNTH_TIEHI_CELL)
lappend arg_list -tielo_port $::env(SYNTH_TIELO_CELL)
lappend arg_list -work_dir $::env(STEP_DIR)
lappend arg_list -abc_logfile $::env(_RMP_ABC_LOG)
lappend arg_list -liberty_file $::env(_RMP_LIB)
lappend arg_list -target $::env(RMP_TARGET)
if { [info exists ::env(RMP_DEPTH_THRESHOLD)] } {
    lappend arg_list -depth_threshold $::env(RMP_DEPTH_THRESHOLD)
}
if { [info exists ::env(RMP_SLACK_THRESHOLD)] } {
    lappend arg_list -slack_threshold $::env(RMP_SLACK_THRESHOLD)
}
restructure {*}$arg_list
remove_buffers
if { $::env(RMP_TARGET) == "timing" } {
    repair_design
    repair_timing
    remove_buffers
}
write_views
report_design_area_metrics
