// mid.sv: 中间层模块, 实例化 leaf
module mid (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] sum,
    output logic [7:0] diff
);
    leaf u_l1(.clk(clk), .rst_n(rst_n), .din(a), .dout(sum));
    leaf u_l2(.clk(clk), .rst_n(rst_n), .din(b), .dout(diff));
endmodule
