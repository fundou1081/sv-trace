// ============================================================================
// PipelineAnalyzer 测试用例 - 流水线分析
// ============================================================================

// Test 1: 简单2级流水线
module test_pipe_2stage;
    logic clk;
    logic [7:0] stage1, stage2, stage3;
    
    always_ff @(posedge clk) begin
        stage1 <= 8'h00;
        stage2 <= stage1;
        stage3 <= stage2;
    end
endmodule

// Test 2: 3级流水线
module test_pipe_3stage;
    logic clk;
    logic [7:0] s1, s2, s3, s4;
    
    always_ff @(posedge clk) begin
        s1 <= 8'h00;
        s2 <= s1;
        s3 <= s2;
        s4 <= s3;
    end
endmodule

// Test 3: 4级流水线
module test_pipe_4stage;
    logic clk;
    logic [7:0] s1, s2, s3, s4, s5;
    
    always_ff @(posedge clk) begin
        s1 <= 8'h00;
        s2 <= s1;
        s3 <= s2;
        s4 <= s3;
        s5 <= s4;
    end
endmodule

// Test 4: 流水线带使能
module test_pipe_enable;
    logic clk, enable;
    logic [7:0] s1, s2, s3;
    
    always_ff @(posedge clk) begin
        if (enable) begin
            s1 <= 8'h00;
            s2 <= s1;
            s3 <= s2;
        end
    end
endmodule

// Test 5: 流水线带复位
module test_pipe_reset;
    logic clk, rst_n;
    logic [7:0] s1, s2, s3;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s1 <= 8'h00;
            s2 <= 8'h00;
            s3 <= 8'h00;
        end else begin
            s1 <= 8'h01;
            s2 <= s1;
            s3 <= s2;
        end
    end
endmodule

// Test 6: 流水线带旁路
module test_pipe_bypass;
    logic clk;
    logic [7:0] in, s1, s2, out;
    
    always_ff @(posedge clk) begin
        s1 <= in;
        s2 <= s1;
        out <= in;  // 旁路
    end
endmodule

// Test 7: 流水线带选择
module test_pipe_select;
    logic clk, sel;
    logic [7:0] in0, in1, s1, s2, out;
    
    always_ff @(posedge clk) begin
        s1 <= sel ? in1 : in0;
        s2 <= s1;
        out <= s2;
    end
endmodule

// Test 8: 多周期运算
module test_pipe_compute;
    logic clk;
    logic [7:0] a, b, mul1, mul2, result;
    
    always_ff @(posedge clk) begin
        mul1 <= a * b;
        mul2 <= mul1;
        result <= mul2;
    end
endmodule

// Test 9: 嵌套流水线
module test_pipe_nested;
    logic clk;
    logic [7:0] outer1, outer2, outer3;
    logic [7:0] inner1, inner2, inner3;
    
    always_ff @(posedge clk) begin
        outer1 <= 8'h00;
        outer2 <= outer1;
        outer3 <= outer2;
        
        inner1 <= outer1;
        inner2 <= inner1;
        inner3 <= inner2;
    end
endmodule

// Test 10: 反馈流水线
module test_pipe_feedback;
    logic clk;
    logic [7:0] counter;
    
    always_ff @(posedge clk)
        counter <= counter + 1;
endmodule

// Test 11: FIFO流水线
module test_pipe_fifo;
    logic clk, wr_en, rd_en;
    logic [7:0] din, dout;
    logic [7:0] mem [0:3];
    logic [1:0] wr_ptr, rd_ptr;
    
    always_ff @(posedge clk) begin
        if (wr_en)
            mem[wr_ptr] <= din;
        if (rd_en)
            dout <= mem[rd_ptr];
    end
endmodule

// Test 12: 移位流水线
module test_pipe_shift;
    logic clk;
    logic [7:0] shift_reg;
    
    always_ff @(posedge clk) begin
        shift_reg <= {shift_reg[6:0], 1'b0};
    end
endmodule

// Test 13: 计数器流水线
module test_pipe_counter;
    logic clk;
    logic [7:0] count1, count2, count3;
    
    always_ff @(posedge clk) begin
        count1 <= count1 + 1;
        count2 <= count1;
        count3 <= count2;
    end
endmodule

// Test 14: 加法器流水线
module test_pipe_adder;
    logic clk;
    logic [7:0] a, b, sum1, sum2, sum3;
    
    always_ff @(posedge clk) begin
        sum1 <= a + b;
        sum2 <= sum1;
        sum3 <= sum2;
    end
endmodule

// Test 15: 乘法器流水线
module test_pipe_mult;
    logic clk;
    logic [7:0] a, b, prod1, prod2;
    
    always_ff @(posedge clk) begin
        prod1 <= a * b;
        prod2 <= prod1;
    end
endmodule

// Test 16: 比较器流水线
module test_pipe_compare;
    logic clk;
    logic [7:0] a, b, gt1, gt2;
    
    always_ff @(posedge clk) begin
        gt1 <= (a > b) ? 8'h01 : 8'h00;
        gt2 <= gt1;
    end
endmodule

// Test 17: 多路选择流水线
module test_pipe_mux;
    logic clk;
    logic [7:0] in0, in1, in2, in3;
    logic [1:0] sel;
    logic [7:0] sel1, sel2, out;
    
    always_ff @(posedge clk) begin
        case (sel)
            2'b00: sel1 <= in0;
            2'b01: sel1 <= in1;
            2'b10: sel1 <= in2;
            default: sel1 <= in3;
        endcase
        sel2 <= sel1;
        out <= sel2;
    end
endmodule

// Test 18: 条件流水线
module test_pipe_cond;
    logic clk, enable;
    logic [7:0] data, d1, d2;
    
    always_ff @(posedge clk) begin
        if (enable) begin
            d1 <= data;
            d2 <= d1;
        end
    end
endmodule

// Test 19: 双端口流水线
module test_pipe_dual;
    logic clk;
    logic [7:0] a1, a2, b1, b2, c1, c2;
    
    always_ff @(posedge clk) begin
        a1 <= 8'h00;
        a2 <= 8'h01;
        b1 <= a1;
        b2 <= a2;
        c1 <= b1;
        c2 <= b2;
    end
endmodule

// Test 20: 异步流水线
module test_pipe_async;
    logic clk_a, clk_b;
    logic [7:0] reg_a, reg_b;
    
    always_ff @(posedge clk_a)
        reg_a <= 8'h01;
    
    always_ff @(posedge clk_b)
        reg_b <= reg_a;
endmodule
