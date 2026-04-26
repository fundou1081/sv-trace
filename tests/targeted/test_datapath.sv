// ============================================================================
// Datapath 测试用例 - 数据路径分析
// ============================================================================

// Test 1: 简单数据流
module test_dp_simple;
    logic [7:0] a, b, result;
    
    assign result = a + b;
endmodule

// Test 2: 双输入
module test_dp_2input;
    logic [7:0] a, b, c, result;
    
    assign result = a + b + c;
endmodule

// Test 3: 多输入
module test_dp_3input;
    logic [7:0] a, b, c, d, result;
    
    assign result = a + b + c + d;
endmodule

// Test 4: 算术路径
module test_dp_arith;
    logic [7:0] a, b, result;
    
    assign result = a + b;
endmodule

// Test 5: 逻辑路径
module test_dp_logic;
    logic [7:0] a, b, result;
    
    assign result = a & b;
endmodule

// Test 6: 移位路径
module test_dp_shift;
    logic [7:0] data;
    logic [2:0] shamt;
    logic [7:0] result;
    
    assign result = data << shamt;
endmodule

// Test 7: 比较路径
module test_dp_compare;
    logic [7:0] a, b, gt, lt;
    
    assign gt = (a > b) ? 8'h01 : 8'h00;
    assign lt = (a < b) ? 8'h01 : 8'h00;
endmodule

// Test 8: 选择路径
module test_dp_select;
    logic [7:0] a, b, sel, result;
    
    assign result = sel ? a : b;
endmodule

// Test 9: 多路选择
module test_dp_mux4;
    logic [7:0] in0, in1, in2, in3;
    logic [1:0] sel;
    logic [7:0] result;
    
    assign result = (sel == 2'b00) ? in0 :
                 (sel == 2'b01) ? in1 :
                 (sel == 2'b10) ? in2 : in3;
endmodule

// Test 10: 条件数据流
module test_dp_cond;
    logic [7:0] a, b, en, result;
    
    assign result = en ? a : b;
endmodule

// Test 11: 嵌套运算
module test_dp_nested;
    logic [7:0] a, b, c, result;
    
    assign result = (a + b) * c;
endmodule

// Test 12: 双路数据流
module test_dp_dual;
    logic [7:0] a, b, r1, r2;
    
    assign r1 = a + 1;
    assign r2 = b + 1;
endmodule

// Test 13: 反馈数据流
module test_dp_feedback;
    logic clk;
    logic [7:0] counter;
    
    always_ff @(posedge clk)
        counter <= counter + 1;
endmodule

// Test 14: 流水线数据流
module test_dp_pipe;
    logic clk;
    logic [7:0] s1, s2, s3;
    
    always_ff @(posedge clk) begin
        s1 <= 8'h00;
        s2 <= s1;
        s3 <= s2;
    end
endmodule

// Test 15: 双数据流
module test_dp_double;
    logic clk;
    logic [7:0] a, b, result;
    
    always_ff @(posedge clk) begin
        result <= a + b;
    end
endmodule

// Test 16: 乘法数据流
module test_dp_mult;
    logic clk;
    logic [7:0] a, b, prod;
    
    always_ff @(posedge clk)
        prod <= a * b;
endmodule

// Test 17: 除法数据流
module test_dp_div;
    logic [7:0] a, b, quot;
    
    assign quot = a / b;
endmodule

// Test 18: 拼接数据流
module test_dp_concat;
    logic [3:0] a, b;
    logic [7:0] result;
    
    assign result = {a, b};
endmodule

// Test 19: 位选择数据流
module test_dp_bitsel;
    logic [15:0] data;
    logic [7:0] result;
    
    assign result = data[7:0];
endmodule

// Test 20: 归约数据流
module test_dp_reduction;
    logic [7:0] data;
    logic result;
    
    assign result = |data;
endmodule
