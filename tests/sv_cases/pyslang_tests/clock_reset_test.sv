// ============================================================================
// Clock/Reset 测试用例 - 验证 pyslang AST 解析时钟复位语法
// ============================================================================

// Test 1: 单时钟同步复位
module sync_reset_module(
    input clk,
    input rst,
    input [7:0] data_in,
    output reg [7:0] data_out
);
    always @(posedge clk) begin
        if (rst)
            data_out <= 0;
        else
            data_out <= data_in;
    end
endmodule

// Test 2: 单时钟异步复位
module async_reset_module(
    input clk,
    input rst_n,
    input [7:0] data_in,
    output reg [7:0] data_out
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data_out <= 0;
        else
            data_out <= data_in;
    end
endmodule

// Test 3: 多时钟
module multi_clock_module(
    input clk_a,
    input clk_b,
    input [7:0] data_a,
    input [7:0] data_b,
    output [7:0] out_a,
    output [7:0] out_b
);
    always @(posedge clk_a) begin
        out_a <= data_a;
    end
    always @(posedge clk_b) begin
        out_b <= data_b;
    end
endmodule

// Test 4: 门控时钟
module gated_clock_module(
    input clk,
    input clk_en,
    input [7:0] data_in,
    output [7:0] data_out
);
    wire gated_clk = clk & clk_en;
    always @(posedge gated_clk) begin
        data_out <= data_in;
    end
endmodule

// Test 5: 双沿时钟
module dual_edge_module(
    input clk,
    input data_in,
    output reg data_out
);
    always @(posedge clk) begin
        data_out <= data_in;
    end
    always @(negedge clk) begin
        data_out <= ~data_in;
    end
endmodule

// Test 6: 多复位域
module multi_reset_domain(
    input clk,
    input rst_n,
    input rst_shadowed_n,
    input [7:0] data_in,
    output [7:0] data_out
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data_out <= 0;
        else
            data_out <= data_in;
    end
endmodule
