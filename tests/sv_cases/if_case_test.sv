
module top(
    input clk,
    input [7:0] data_in,
    input [1:0] mode,
    output [7:0] result
);
    
    reg [7:0] temp;
    
    // case多路选择
    always @(posedge clk) begin
        case (mode)
            2'd0: temp <= data_in + 1;    // add
            2'd1: temp <= data_in - 1;    // sub
            2'd2: temp <= data_in & 8'hFF; // and
            2'd3: temp <= data_in | 8'h00; // or
        endcase
    end
    
    always @(posedge clk)
        result <= temp;
endmodule
