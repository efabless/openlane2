yosys -import

read_verilog $::env(VERILOG_FILES)
synth -top $::env(DESIGN_NAME)
techmap; opt
dfflibmap -liberty trimmed.lib
abc -liberty trimmed.lib

write_verilog $::env(SAVE_NETLIST)


