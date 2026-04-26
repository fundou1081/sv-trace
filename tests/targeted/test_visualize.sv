// ============================================================================
// Visualize 测试用例 - 可视化
// ============================================================================

// Test 1: 简单可视化
module test_viz_simple;
    logic [7:0] sig;
    
    assign sig = 8'h00;
endmodule

// Test 2: 层次可视化
module test_viz_hierarchy;
    logic clk;
    logic [7:0] top_sig;
    
    child_viz u_child (.clk(clk), .sig(top_sig));
endmodule

module child_viz (
    input  logic clk,
    input  logic [7:0] sig
);
    logic [7:0] reg_sig;
    
    always_ff @(posedge clk)
        reg_sig <= sig;
endmodule

// Test 3: 模块连接可视化
module test_viz_conn;
    logic clk;
    logic [7:0] a, b, out;
    
    my_add u_add (.a(a), .b(b), .out(out));
endmodule

module my_add (
    input  logic [7:0] a, b,
    output logic [7:0] out
);
    assign out = a + b;
endmodule

// Test 4: 信号追踪可视化
module test_viz_signal;
    logic clk;
    logic [7:0] sig1, sig2;
    
    always_ff @(posedge clk) begin
        sig1 <= 8'h00;
        sig2 <= sig1;
    end
endmodule

// Test 5: 时钟域可视化
module test_viz_clock;
    logic clk_a, clk_b;
    logic [7:0] reg_a, reg_b;
    
    always_ff @(posedge clk_a)
        reg_a <= 8'h01;
    
    always_ff @(posedge clk_b)
        reg_b <= 8'h01;
endmodule

// Test 6: 状态机可视化
module test_viz_fsm;
    logic clk, rst_n;
    logic [1:0] state;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= 2'b00;
        else
            state <= state + 1;
    end
endmodule

// Test 7: 复位可视化
module test_viz_reset;
    logic clk, rst_n;
    logic [7:0] counter;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            counter <= 8'h00;
        else
            counter <= counter + 1;
    end
endmodule

// Test 8: 端口可视化
module test_viz_port (
    input  logic clk,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    always_ff @(posedge clk)
        data_out <= data_in;
endmodule

// Test 9: 参数化可视化
module test_viz_param #(
    parameter WIDTH = 8
) (
    input  logic clk,
    input  logic [WIDTH-1:0] data,
    output logic [WIDTH-1:0] out
);
    always_ff @(posedge clk)
        out <= data;
endmodule

// Test 10: 接口可视化
module test_viz_interface;
    logic clk;
    logic [7:0] sig;
    
    simple_if if1 (.*);
endmodule

interface simple_if (
    input logic clk
);
    logic [7:0] data;
endinterface

// Test 11: 生成块可视化
module test_viz_gen;
    logic clk;
    logic [7:0] out [0:3];
    
    genvar i;
    generate
        for (i = 0; i < 4; i++) begin : gen_vis
            always_ff @(posedge clk)
                out[i] <= 8'(i);
        end
    endgenerate
endmodule

// Test 12: 函数可视化
module test_viz_func;
    logic [7:0] a, b, result;
    
    always_comb begin
        result = my_func(a, b);
    end
    
    function [7:0] my_func(input [7:0] x, y);
        begin
            my_func = x + y;
        end
    endfunction
endmodule

// Test 13: 任务可视化
module test_viz_task;
    logic clk;
    logic [7:0] data;
    
    always_ff @(posedge clk)
        data <= 8'h00;
endmodule

// Test 14: 数组可视化
module test_viz_array;
    logic [7:0] mem [0:15];
    logic [3:0] addr;
    logic [7:0] data;
    
    assign data = mem[addr];
endmodule

// Test 15: 多维数组可视化
module test_viz_array2d;
    logic [7:0] mem [0:3][0:3];
    logic [1:0] x, y;
    logic [7:0] data;
    
    assign data = mem[x][y];
endmodule

// Test 16: 结构体可视化
module test_viz_struct;
    logic clk;
    logic [7:0] data;
    
    always_ff @(posedge clk)
        data <= 8'h00;
endmodule

// Test 17: 包可视化
module test_viz_pkg;
    logic [7:0] data;
    
    assign data = 8'h00;
endmodule

// Test 18: 别名可视化
module test_viz_alias;
    logic [7:0] sig1, sig2;
    
    assign sig2 = sig1;
endmodule

// Test 19: 跨模块可视化
module test_viz_cross;
    logic clk;
    logic [7:0] top_sig;
    
    sub_viz u_sub (.clk(clk), .sig(top_sig));
endmodule

module sub_viz (
    input  logic clk,
    input  logic [7:0] sig
);
    logic [7:0] reg_sig;
    
    always_ff @(posedge clk)
        reg_sig <= sig;
endmodule

// Test 20: 复杂层次可视化
module test_viz_complex;
    logic clk;
    logic [7:0] level1, level2, level3;
    logic [7:0] result;
    
    always_ff @(posedge clk) begin
        level1 <= 8'h00;
        level2 <= level1;
        level3 <= level2;
        result <= level3;
    end
endmodule
