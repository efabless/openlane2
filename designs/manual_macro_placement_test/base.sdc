###############################################################################
# Created by write_sdc
# Wed Oct  6 21:55:22 2021
###############################################################################
current_design manual_macro_placement_test
###############################################################################
# Timing Constraints
###############################################################################
create_clock -name clk1 -period 100.0000 [get_ports {clk1}]
create_clock -name clk2 -period 100.0000 [get_ports {clk2}]
set_input_delay 20.0000 -clock [get_clocks clk1] -add_delay [get_ports {x1[0]}]
set_input_delay 20.0000 -clock [get_clocks clk1] -add_delay [get_ports {x1[10]}]
set_input_delay 20.0000 -clock [get_clocks clk1] -add_delay [get_ports {x1[11]}]
set_input_delay 20.0000 -clock [get_clocks clk1] -add_delay [get_ports {x1[12]}]
set_input_delay 20.0000 -clock [get_clocks clk1] -add_delay [get_ports {x1[13]}]
set_input_delay 20.0000 -clock [get_clocks clk1] -add_delay [get_ports {x1[14]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[15]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[16]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[17]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[18]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[19]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[1]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[20]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[21]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[22]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[23]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[24]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[25]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[26]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[27]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[28]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[29]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[2]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[30]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[31]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[3]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[4]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[5]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[6]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[7]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {x1[8]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x1[9]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[0]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[10]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[11]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[12]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[13]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[14]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[15]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[16]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[17]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[18]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[19]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[1]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[20]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[21]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[22]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[23]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[24]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[25]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[26]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[27]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[28]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[29]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[2]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[30]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[31]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[3]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[4]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[5]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[6]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[7]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[8]}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {x2[9]}]
set_input_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {y1}]
set_input_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {y2}]
set_output_delay 20.0000 -clock [get_clocks clk1]  -add_delay [get_ports {p1}]
set_output_delay 20.0000 -clock [get_clocks clk2]  -add_delay [get_ports {p2}]
###############################################################################
# Environment
###############################################################################
set_load -pin_load 0.0177 [get_ports {p1}]
set_load -pin_load 0.0177 [get_ports {p2}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {clk1}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {clk2}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {rst1}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {rst2}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {y1}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {y2}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[31]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[30]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[29]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[28]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[27]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[26]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[25]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[24]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[23]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[22]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[21]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[20]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[19]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[18]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[17]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[16]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[15]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[14]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[13]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[12]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[11]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[10]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[9]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[8]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[7]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[6]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[5]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[4]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[3]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[2]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[1]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x1[0]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[31]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[30]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[29]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[28]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[27]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[26]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[25]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[24]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[23]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[22]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[21]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[20]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[19]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[18]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[17]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[16]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[15]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[14]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[13]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[12]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[11]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[10]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[9]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[8]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[7]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[6]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[5]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[4]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[3]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[2]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[1]}]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_8 -pin {Y} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {x2[0]}]
###############################################################################
# Design Rules
###############################################################################
set_max_fanout 5.0000 [current_design]
