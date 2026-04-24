
module top(input clk, rst_n, input [7:0] data_in, valid, output [7:0] data_out);
  always @(posedge clk) if(!rst_n) data_out<=0; else if(valid) data_out<=data_in+1;
endmodule
