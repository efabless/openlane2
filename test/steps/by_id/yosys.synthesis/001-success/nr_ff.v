module nr_ff(
    input clk,
    input a,
    output reg b
);
    always_ff @(posedge clk) begin
        b <= a;
    end

endmodule