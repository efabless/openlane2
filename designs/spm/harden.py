from openlane import Flow

Classic = Flow.get("Classic")

flow = Classic(
    {
        "PDK": "sky130A",
        "DESIGN_NAME": "spm",
        "VERILOG_FILES": ["./src/spm.v"],
        "CLOCK_PORT": "clk",
        "CLOCK_PERIOD": 10,
    },
    spm="sky130_fd_sc_hd",
    design_dir=".",
)

flow.start()
