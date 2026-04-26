// ============================================================================
// TimingPath 测试用例 - 时序路径分析
// ============================================================================

// Test 1: Reg2Reg路径
module test_tp_reg2reg;
    logic clk;
    logic [7:0] r1, r2;
    
    always_ff @(posedge clk)
        r2 <= r1 + 1;
endmodule

// Test 2: In2Reg路径
module test_tp_in2reg;
    logic clk;
    logic [7:0] data_in, reg_q;
    
    always_ff @(posedge clk)
        reg_q <= data_in + 1;
endmodule

// Test 3: Reg2Out路径
module test_tp_reg2out;
    logic clk;
    logic [7:0] reg_q, data_out;
    
    always_ff @(posedge clk)
        reg_q <= 8'h00;
    
    assign data_out = reg_q + 1;
endmodule

// Test 4: In2Out路径
module test_tp_in2out;
    logic [7:0] data_in, data_out;
    
    assign data_out = data_in + 1;
endmodule

// Test 5: 多级路径
module test_tp_multi;
    logic clk;
    logic [7:0] r1, r2, r3;
    
    always_ff @(posedge clk) begin
        r2 <= r1 + 1;
        r3 <= r2 + 1;
    end
endmodule

// Test 6: 组合逻辑路径
module test_tp_comb;
    logic [7:0] a, b, c, result;
    
    assign b = a + 1;
    assign c = b + 1;
    assign result = c + 1;
endmodule

// Test 7: 混合路径
module test_tp_mixed;
    logic clk;
    logic [7:0] data_in, r1, comb, r2;
    
    always_ff @(posedge clk)
        r1 <= data_in + 1;
    
    assign comb = r1 + 1;
    
    always_ff @(posedge clk)
        r2 <= comb + 1;
endmodule

// Test 8: 反馈路径
module test_tp_feedback;
    logic clk;
    logic [7:0] counter;
    
    always_ff @(posedge clk)
        counter <= counter + 1;
endmodule

// Test 9: 跨模块路径
module test_tp_cross;
    logic clk;
    logic [7:0] sig;
    
    tp_child u_child (.clk(clk), .sig(sig));
endmodule

module tp_child (
    input  logic clk,
    input  logic [7:0] sig
);
    logic [7:0] reg_sig;
    
    always_ff @(posedge clk)
        reg_sig <= sig + 1;
endmodule

// Test 10: 多时钟域路径
module test_tp_multiclock;
    logic clk_a, clk_b;
    logic [7:0] r_a, r_b;
    
    always_ff @(posedge clk_a)
        r_a <= 8'h01;
    
    always_ff @(posedge clk_b)
        r_b <= r_a + 1;
endmodule

// Test 11: 流水线路径
module test_tp_pipe;
    logic clk;
    logic [7:0] s1, s2, s3, s4;
    
    always_ff @(posedge clk) begin
        s1 <= 8'h00;
        s2 <= s1 + 1;
        s3 <= s2 + 1;
        s4 <= s3 + 1;
    end
endmodule

// Test 12: 选择路径
module test_tp_mux;
    logic clk;
    logic [7:0] in0, in1, sel, out;
    
    always_ff @(posedge clk) begin
        if (sel)
            out <= in1;
        else
            out <= in0;
    end
endmodule

// Test 13: 条件路径
module test_tp_cond;
    logic clk, enable;
    logic [7:0] data, out;
    
    always_ff @(posedge clk) begin
        if (enable)
            out <= data + 1;
    end
endmodule

// Test 14: 旁路路径
module test_tp_bypass;
    logic clk;
    logic [7:0] in, s1, out;
    
    always_ff @(posedge clk) begin
        s1 <= in + 1;
        out <= in;  // 旁路
    end
endmodule

// Test 15: 长路径
module test_tp_long;
    logic [7:0] a, b, c, d, e, f, g, h, result;
    
    assign b = a + 1;
    assign c = b + 1;
    assign d = c + 1;
    assign e = d + 1;
    assign f = e + 1;
    assign g = f + 1;
    assign h = g + 1;
    assign result = h + 1;
endmodule

// Test 16: 短路径
module test_tp_short;
    logic clk;
    logic [7:0] r1, r2;
    
    always_ff @(posedge clk)
        r2 <= r1 + 1;
endmodule

// Test 17: 多路径
module test_tp_multi_path;
    logic clk;
    logic [7:0] in, r1, r2, r3;
    
    always_ff @(posedge clk) begin
        r1 <= in + 1;
        r2 <= in + 2;
        r3 <= in + 3;
    end
endmodule

// Test 18: 复位路径
module test_tp_reset;
    logic clk, rst_n;
    logic [7:0] counter;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            counter <= 8'h00;
        else
            counter <= counter + 1;
    end
endmodule

// Test 19: 使能路径
module test_tp_enable;
    logic clk, enable;
    logic [7:0] data, out;
    
    always_ff @(posedge clk) begin
        if (enable)
            out <= data + 1;
    end
endmodule

// Test 20: 双向路径
module test_tp_bidir;
    logic clk;
    logic [7:0] a, b;
    
    always_ff @(posedge clk) begin
        a <= 8'h00;
        b <= a + 1;
    end
endmodule
