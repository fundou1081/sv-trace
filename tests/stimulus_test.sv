
module top (
    input clk, rst_n,
    input [7:0] data_in,
    input valid,
    input [2:0] mode,
    output [7:0] data_out
);
    
    reg [7:0] temp;
    reg [7:0] result;
    
    // Stage 1: temp = data_in + mode
    always @(posedge clk) begin
        if (!rst_n) begin
            temp <= 0;
        end else if (valid) begin
            temp <= data_in + mode;
        end
    end
    
    // Stage 2: result = temp + 1
    always @(posedge clk) begin
        if (!rst_n) begin
            result <= 0;
        end else begin
            result <= temp + 1;
        end
    end
endmodule
