module test_dut (
    input  clk,
    input  rst_n,
    input  [7:0] data_in,
    input         valid,
    input  [1:0] mode,
    output [7:0] data_out,
    output       ready
);
    
    always @(posedge clk) begin
        if (!rst_n) begin
            data_out <= 0;
            ready <= 0;
        end else if (valid) begin
            data_out <= data_in + 1;
            ready <= 1;
        end
    end
endmodule
