// ============================================================================
// TimingDepth 测试用例 - 时序深度分析
// ============================================================================

// Test 1: 1级深度
module test_td_1;
    logic clk;
    logic [7:0] r1, r2;
    
    always_ff @(posedge clk)
        r2 <= r1 + 1;
endmodule

// Test 2: 2级深度
module test_td_2;
    logic clk;
    logic [7:0] r1, r2, r3;
    
    always_ff @(posedge clk) begin
        r2 <= r1 + 1;
        r3 <= r2 + 1;
    end
endmodule

// Test 3: 3级深度
module test_td_3;
    logic clk;
    logic [7:0] r1, r2, r3, r4;
    
    always_ff @(posedge clk) begin
        r2 <= r1 + 1;
        r3 <= r2 + 1;
        r4 <= r3 + 1;
    end
endmodule

// Test 4: 4级深度
module test_td_4;
    logic clk;
    logic [7:0] r1, r2, r3, r4, r5;
    
    always_ff @(posedge clk) begin
        r2 <= r1 + 1;
        r3 <= r2 + 1;
        r4 <= r3 + 1;
        r5 <= r4 + 1;
    end
endmodule

// Test 5: 组合深度
module test_td_comb;
    logic [7:0] a, b, c;
    
    assign b = a + 1;
    assign c = b + 1;
endmodule

// Test 6: 深度嵌套
module test_td_nested;
    logic clk;
    logic [7:0] outer1, outer2;
    logic [7:0] inner1, inner2;
    
    always_ff @(posedge clk) begin
        outer2 <= outer1 + 1;
        inner2 <= inner1 + 1;
    end
endmodule

// Test 7: 混合深度
module test_td_mixed;
    logic clk;
    logic [7:0] data_in, r1, comb, r2;
    
    always_ff @(posedge clk)
        r1 <= data_in + 1;
    
    assign comb = r1 + 1;
    
    always_ff @(posedge clk)
        r2 <= comb + 1;
endmodule

// Test 8: 可变深度
module test_td_var;
    logic clk;
    logic [7:0] r1, r2, r3;
    
    always_ff @(posedge clk) begin
        r2 <= r1;
        r3 <= r2;
    end
endmodule

// Test 9: 反馈深度
module test_td_feedback;
    logic clk;
    logic [7:0] counter;
    
    always_ff @(posedge clk)
        counter <= counter + 1;
endmodule

// Test 10: 旁路深度
module test_td_bypass;
    logic clk;
    logic [7:0] in, s1, out;
    
    always_ff @(posedge clk) begin
        s1 <= in + 1;
        out <= in;
    end
endmodule

// Test 11: 选择深度
module test_td_mux;
    logic clk;
    logic [7:0] in0, in1, sel, out;
    
    always_ff @(posedge clk) begin
        out <= sel ? in1 : in0;
    end
endmodule

// Test 12: 条件深度
module test_td_cond;
    logic clk, enable;
    logic [7:0] data, out;
    
    always_ff @(posedge clk) begin
        if (enable)
            out <= data + 1;
    end
endmodule

// Test 13: 多路径深度
module test_td_multi_path;
    logic clk;
    logic [7:0] in, r1, r2, r3;
    
    always_ff @(posedge clk) begin
        r1 <= in + 1;
        r2 <= in + 2;
        r3 <= in + 3;
    end
endmodule

// Test 14: 流水线深度
module test_td_pipe;
    logic clk;
    logic [7:0] s1, s2, s3, s4, s5;
    
    always_ff @(posedge clk) begin
        s2 <= s1 + 1;
        s3 <= s2 + 1;
        s4 <= s3 + 1;
        s5 <= s4 + 1;
    end
endmodule

// Test 15: 跨时钟域深度
module test_td_cdc;
    logic clk_a, clk_b;
    logic [7:0] r_a, r_b;
    
    always_ff @(posedge clk_a)
        r_a <= 8'h01;
    
    always_ff @(posedge clk_b)
        r_b <= r_a + 1;
endmodule

// Test 16: FIFO深度
module test_td_fifo;
    logic clk;
    logic [7:0] din, dout;
    logic [2:0] wr_ptr, rd_ptr;
    
    always_ff @(posedge clk) begin
        wr_ptr <= wr_ptr + 1;
        rd_ptr <= rd_ptr + 1;
    end
endmodule

// Test 17: 移位寄存器深度
module test_td_shift;
    logic clk;
    logic [7:0] shift_reg;
    
    always_ff @(posedge clk) begin
        shift_reg <= {shift_reg[6:0], 1'b0};
    end
endmodule

// Test 18: 计数器深度
module test_td_counter;
    logic clk;
    logic [7:0] count1, count2, count3;
    
    always_ff @(posedge clk) begin
        count1 <= count1 + 1;
        count2 <= count1;
        count3 <= count2;
    end
endmodule

// Test 19: 复杂树深度
module test_td_tree;
    logic clk;
    logic [7:0] r1, r2, r3, r4;
    
    always_ff @(posedge clk) begin
        r1 <= 8'h00;
        r2 <= r1 + 1;
        r3 <= r1 + 2;
        r4 <= r2 + r3;
    end
endmodule

// Test 20: 状态机深度
module test_td_fsm;
    logic clk, rst_n;
    logic [1:0] state;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= 2'b00;
        else
            state <= state + 1;
    end
endmodule
