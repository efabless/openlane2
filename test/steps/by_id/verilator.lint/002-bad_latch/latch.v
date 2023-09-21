module latch_bad(input clk, input a, input en, output b);

reg v;

always @ *
    if (en)
        v <= a;

assign b = v;

endmodule