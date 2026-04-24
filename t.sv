
module mem_test(input clk, input [7:0] in, input en, input [3:0] addr, output [7:0] out);
reg [7:0] mem [0:15];
always @(posedge clk) if(en) mem[addr] <= in;
assign out = mem[addr];
endmodule
