
module mem(input clk,input [7:0] din,input en,input [3:0] ad,output [7:0] dout);
reg [7:0] mem [0:15];
always @(posedge clk) if(en) mem[ad]<=din;
assign dout=mem[ad];
endmodule
