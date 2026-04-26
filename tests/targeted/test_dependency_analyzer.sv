// ============================================================================
// DependencyAnalyzer 测试用例 - 验证依赖分析功能
// ============================================================================

// Test 1: 简单组合逻辑依赖
module test_dep_simple_comb;
    logic [7:0] a, b, c, result;
    
    assign result = a + b;  // result依赖a和b
endmodule

// Test 2: 时序逻辑依赖
module test_dep_seq;
    logic clk;
    logic [7:0] d, q;
    
    always_ff @(posedge clk)
        q <= d;  // q依赖d (D触发器)
endmodule

// Test 3: 多级组合逻辑依赖链
module test_dep_chain;
    logic [7:0] a, b, c, d, result;
    
    assign b = a + 1;
    assign c = b + 1;
    assign d = c + 1;
    assign result = d + 1;
endmodule

// Test 4: 条件依赖
module test_dep_conditional;
    logic [7:0] a, b, sel, result;
    
    assign result = sel ? a : b;  // result依赖a, b, sel
endmodule

// Test 5: 循环依赖检测
module test_dep_circular;
    logic [7:0] a, b, c;
    
    assign a = b + 1;
    assign b = c + 1;
    assign c = a + 1;  // 形成 a->b->c->a 循环
endmodule

// Test 6: 跨模块依赖
module test_dep_cross;
    logic clk;
    logic [7:0] sig;
    
    cross_child inst (.clk(clk), .sig(sig));
endmodule

module cross_child (
    input  logic clk,
    input  logic [7:0] sig
);
    logic [7:0] reg_sig;
    
    always_ff @(posedge clk)
        reg_sig <= sig;
endmodule

// Test 7: 复位信号的依赖
module test_dep_reset;
    logic clk, rst_n;
    logic [7:0] counter;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            counter <= 8'h00;
        else
            counter <= counter + 1;
    end
endmodule

// Test 8: 生成块的依赖
module test_dep_generate;
    logic clk;
    logic [7:0] out [0:3];
    
    genvar i;
    generate
        for (i = 0; i < 4; i++) begin : gen_dep
            always_ff @(posedge clk)
                out[i] <= 8'(i);
        end
    endgenerate
endmodule

// Test 9: case语句的依赖
module test_dep_case;
    logic [1:0] sel;
    logic [7:0] result;
    
    always_comb begin
        case (sel)
            2'b00: result = 8'hAA;
            2'b01: result = 8'h55;
            2'b10: result = 8'hF0;
            default: result = 8'h00;
        endcase
    end
endmodule

// Test 10: if-else嵌套依赖
module test_dep_nested_if;
    logic a, b, c;
    logic [7:0] result;
    
    always_comb begin
        if (a) begin
            if (b)
                result = 8'h01;
            else
                result = 8'h02;
        end else begin
            result = 8'h00;
        end
    end
endmodule

// Test 11: 多路选择依赖
module test_dep_mux;
    logic [7:0] in0, in1, in2, in3;
    logic [1:0] sel;
    logic [7:0] out;
    
    always_comb begin
        out = in0;
        if (sel[0]) out = in1;
        if (sel[1]) out = in2;
    end
endmodule

// Test 12: 加法链依赖
module test_dep_add_chain;
    logic [7:0] a0, a1, a2, a3, sum;
    
    assign sum = a0 + a1 + a2 + a3;  // 多操作数
endmodule

// Test 13: 比较器依赖
module test_dep_comparison;
    logic [7:0] a, b;
    logic eq, neq, gt, lt;
    
    assign eq = (a == b);
    assign neq = (a != b);
    assign gt = (a > b);
    assign lt = (a < b);
endmodule

// Test 14: 移位操作的依赖
module test_dep_shift;
    logic [7:0] data;
    logic [2:0] shamt;
    logic [7:0] left, right, arith;
    
    assign left = data << shamt;
    assign right = data >> shamt;
    assign arith = data >>> shamt;  // 算术右移
endmodule

// Test 15: 位运算依赖
module test_dep_bitwise;
    logic [7:0] a, b;
    logic [7:0] and_res, or_res, xor_res, not_res;
    
    assign and_res = a & b;
    assign or_res = a | b;
    assign xor_res = a ^ b;
    assign not_res = ~a;
endmodule

// Test 16: 拼接依赖
module test_dep_concat;
    logic [3:0] a, b;
    logic [7:0] combined;
    
    assign combined = {a, b};
endmodule

// Test 17: 重复操作依赖
module test_dep_replication;
    logic [3:0] a;
    logic [7:0] repeated;
    
    assign repeated = {2{a}};  // {{a, a}}
endmodule

// Test 18: 函数调用的依赖
module test_dep_func;
    logic [7:0] a, b, result;
    
    always_comb begin
        result = func_add(a, b);
    end
    
    function [7:0] func_add(input [7:0] x, y);
        begin
            func_add = x + y;
        end
    endfunction
endmodule
