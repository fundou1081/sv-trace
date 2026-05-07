// ============================================================================
// ModuleDependencyAnalyzer 测试用例 - 模块依赖
// ============================================================================

// 叶子模块 (无依赖)
module leaf_a;
    logic clk;
    logic [7:0] data;
endmodule

module leaf_b;
    logic clk;
    logic [7:0] data;
endmodule

// 中间层模块
module middle #(
    parameter WIDTH = 8
)(
    input clk,
    input [WIDTH-1:0] in_data,
    output [WIDTH-1:0] out_data
);
    leaf_a u_leaf();
    assign out_data = in_data;
endmodule

// 顶层模块
module top;
    logic clk;
    logic [7:0] a_data, b_data, mid_data;
    
    leaf_a u_a();
    leaf_b u_b();
    middle #(.WIDTH(8)) u_mid();
    
    assign u_mid.in_data = 8'h00;
    assign a_data = u_a.data;
    assign b_data = u_b.data;
endmodule

// 循环依赖测试
module cycle_a(
    input clk,
    input [7:0] in_a,
    output [7:0] out_a
);
    logic [7:0] temp;
    always_ff @(posedge clk) begin
        temp <= in_a;
    end
    assign out_a = temp;
endmodule

module cycle_b(
    input clk,
    input [7:0] in_b,
    output [7:0] out_b
);
    logic [7:0] temp;
    always_ff @(posedge clk) begin
        temp <= in_b;
    end
    assign out_b = temp;
endmodule
