// ============================================================================
// Performance 测试用例 - 性能分析
// ============================================================================

// Test 1: 简单时序逻辑
module test_perf_seq;
    logic clk;
    logic [7:0] reg_q;
    
    always_ff @(posedge clk)
        reg_q <= 8'h00;
endmodule

// Test 2: 组合逻辑延迟
module test_perf_comb;
    logic [7:0] a, b, c, result;
    
    assign result = (a + b) * c;
endmodule

// Test 3: 嵌套组合
module test_perf_nested;
    logic [7:0] a, b, c, d, result;
    
    assign result = ((a + b) * (c - d));
endmodule

// Test 4: 多级组合
module test_perf_levels;
    logic [7:0] a, b, c, d, e, result;
    
    assign b = a + 1;
    assign c = b + 1;
    assign d = c + 1;
    assign e = d + 1;
    assign result = e + 1;
endmodule

// Test 5: 关键路径
module test_perf_critical;
    logic clk;
    logic [7:0] d, q;
    
    always_ff @(posedge clk)
        q <= d + 1;
endmodule

// Test 6: 长组合链
module test_perf_long_comb;
    logic [7:0] a0, a1, a2, a3, a4;
    logic [7:0] b0, b1, b2, b3, b4;
    logic [7:0] sum;
    
    assign b0 = a0 + 1;
    assign b1 = a1 + b0;
    assign b2 = a2 + b1;
    assign b3 = a3 + b2;
    assign b4 = a4 + b3;
    assign sum = b4;
endmodule

// Test 7: 乘法延迟
module test_perf_mult;
    logic clk;
    logic [7:0] a, b, prod;
    
    always_ff @(posedge clk)
        prod <= a * b;
endmodule

// Test 8: 除法延迟
module test_perf_div;
    logic [7:0] a, b, quot;
    
    assign quot = a / b;
endmodule

// Test 9: 移位延迟
module test_perf_shift;
    logic [7:0] data;
    logic [2:0] shamt;
    logic [7:0] result;
    
    assign result = data << shamt;
endmodule

// Test 10: 比较延迟
module test_perf_compare;
    logic [7:0] a, b;
    logic eq, neq, gt, lt;
    
    assign eq = (a == b);
    assign neq = (a != b);
    assign gt = (a > b);
    assign lt = (a < b);
endmodule

// Test 11: 三元延迟
module test_perf_ternary;
    logic [7:0] a, b, sel, result;
    
    assign result = sel ? a : b;
endmodule

// Test 12: 多路选择延迟
module test_perf_case;
    logic [1:0] sel;
    logic [7:0] result;
    
    always_comb begin
        case (sel)
            2'b00: result = 8'h00;
            2'b01: result = 8'h01;
            2'b10: result = 8'h02;
            default: result = 8'h03;
        endcase
    end
endmodule

// Test 13: 同步性能
module test_perf_sync;
    logic clk;
    logic [7:0] r1, r2, r3;
    
    always_ff @(posedge clk) begin
        r1 <= 8'h00;
        r2 <= r1;
        r3 <= r2;
    end
endmodule

// Test 14: 异步性能
module test_perf_async;
    logic clk_a, clk_b;
    logic [7:0] r1, r2;
    
    always_ff @(posedge clk_a)
        r1 <= 8'h00;
    
    always_ff @(posedge clk_b)
        r2 <= r1;
endmodule

// Test 15: 反馈性能
module test_perf_feedback;
    logic clk;
    logic [7:0] counter;
    
    always_ff @(posedge clk)
        counter <= counter + 1;
endmodule

// Test 16: 流水线吞吐
module test_perf_throughput;
    logic clk;
    logic [7:0] in, out;
    
    always_ff @(posedge clk)
        out <= in + 1;
endmodule

// Test 17: 延迟敏感
module test_perf_latch;
    logic enable;
    logic [7:0] data, result;
    
    always_latch begin
        if (enable)
            result = data;
    end
endmodule

// Test 18: 复杂算术
module test_perf_arith;
    logic [7:0] a, b, c;
    logic [15:0] result;
    
    assign result = (a * b) + c;
endmodule

// Test 19: 多周期运算
module test_perf_multicycle;
    logic clk;
    logic [7:0] a, b, r1, r2;
    
    always_ff @(posedge clk) begin
        r1 <= a + b;
        r2 <= r1;
    end
endmodule

// Test 20: 性能瓶颈
module test_perf_bottleneck;
    logic clk;
    logic [7:0] stage1, stage2, stage3;
    
    always_ff @(posedge clk) begin
        stage1 <= 8'h00;
        stage2 <= stage1 + 1;
        stage3 <= stage2 + stage1;
    end
endmodule
