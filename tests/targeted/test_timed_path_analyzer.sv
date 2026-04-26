// ============================================================================
// TimedPathAnalyzer 测试用例 - 时序路径分析测试
// ============================================================================

// Test 1: 寄存器到寄存器路径
module test_path_reg2reg;
    logic clk;
    logic [7:0] reg_a, reg_b;
    
    always_ff @(posedge clk) begin
        reg_b <= reg_a + 1;
    end
endmodule

// Test 2: 输入到寄存器路径
module test_path_in2reg;
    logic clk;
    logic [7:0] data_in, reg_q;
    
    always_ff @(posedge clk)
        reg_q <= data_in;
endmodule

// Test 3: 寄存器到输出路径
module test_path_reg2out;
    logic clk;
    logic [7:0] reg_q, data_out;
    
    always_ff @(posedge clk)
        reg_q <= 8'h00;
    
    assign data_out = reg_q;
endmodule

// Test 4: 输入到输出路径 (组合)
module test_path_in2out;
    logic [7:0] data_in, data_out;
    
    assign data_out = data_in + 1;
endmodule

// Test 5: 多级组合路径
module test_path_multistage;
    logic [7:0] a, b, c, d, result;
    
    assign b = a + 1;
    assign c = b + 1;
    assign d = c + 1;
    assign result = d + 1;
endmodule

// Test 6: 时序路径上的组合逻辑
module test_path_comb_in_seq;
    logic clk;
    logic [7:0] data_in, reg_a, reg_b;
    logic [7:0] comb_result;
    
    assign comb_result = data_in + 8'h10;
    
    always_ff @(posedge clk) begin
        reg_a <= comb_result;
        reg_b <= reg_a + 1;
    end
endmodule

// Test 7: 多路选择路径
module test_path_mux;
    logic clk;
    logic [7:0] in0, in1, sel, reg_q;
    logic [7:0] mux_out;
    
    assign mux_out = sel ? in1 : in0;
    
    always_ff @(posedge clk)
        reg_q <= mux_out;
endmodule

// Test 8: 反馈路径
module test_path_feedback;
    logic clk;
    logic [7:0] counter;
    
    always_ff @(posedge clk)
        counter <= counter + 1;
endmodule

// Test 9: 跨模块路径
module test_path_cross;
    logic clk;
    logic [7:0] sig;
    
    cross_child u_child (.clk(clk), .sig(sig));
endmodule

module cross_child (
    input  logic clk,
    input  logic [7:0] sig
);
    logic [7:0] reg_sig;
    
    always_ff @(posedge clk)
        reg_sig <= sig;
endmodule

// Test 10: 多时钟域路径
module test_path_multiclock;
    logic clk_a, clk_b;
    logic [7:0] reg_a, reg_b;
    
    always_ff @(posedge clk_a)
        reg_a <= 8'h01;
    
    always_ff @(posedge clk_b)
        reg_b <= reg_a;
endmodule

// Test 11: 流水线路径
module test_path_pipeline;
    logic clk;
    logic [7:0] stage0, stage1, stage2, stage3;
    
    always_ff @(posedge clk) begin
        stage0 <= 8'h00;
        stage1 <= stage0;
        stage2 <= stage1;
        stage3 <= stage2;
    end
endmodule

// Test 12: 移位寄存器路径
module test_path_shift;
    logic clk;
    logic [7:0] shift_reg;
    
    always_ff @(posedge clk) begin
        shift_reg <= {shift_reg[6:0], 1'b0};
    end
endmodule
