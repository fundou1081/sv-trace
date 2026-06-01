// top.sv: 顶层模块, 实例化 mid
module top (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] sw1,
    input  logic [7:0] sw2,
    output logic [7:0] led_sum,
    output logic [7:0] led_diff
);
    mid u_mid(
        .clk(clk), .rst_n(rst_n),
        .a(sw1), .b(sw2),
        .sum(led_sum), .diff(led_diff)
    );
endmodule
