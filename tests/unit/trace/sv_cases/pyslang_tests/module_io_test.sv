// ============================================================================
// Module IO 测试用例 - 验证 pyslang AST 解析端口语法
// ============================================================================

// Test 1: ANSI 风格端口
module ansi_ports(
    input clk,
    input rst_n,
    output [7:0] data,
    output valid
);
endmodule

// Test 2: 带位宽的端口
module sized_ports(
    input [3:0] sel,
    input [31:0] data_in,
    output [31:0] data_out
);
endmodule

// Test 3: 参数化模块
module param_module #(
    parameter WIDTH = 8,
    parameter DEPTH = 16
) (
    input clk,
    input [WIDTH-1:0] data_in,
    output [WIDTH-1:0] data_out
);
endmodule

// Test 4: 多时钟模块
module multi_clock_module(
    input clk_a,
    input clk_b,
    input rst_n,
    output [7:0] data_a,
    output [7:0] data_b
);
endmodule

// Test 5: 复杂端口类型
module complex_ports(
    input logic clk,
    input logic [7:0] data,
    output logic [7:0] result,
    output reg ready
);
endmodule

// Test 6: 多模块文件
module top_module(
    input clk,
    output [7:0] out
);
endmodule

module sub_module(
    input [7:0] in,
    output [7:0] out
);
endmodule
