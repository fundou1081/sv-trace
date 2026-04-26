// ============================================================================
// LoadTracer 底层功能测试
// 测试 LoadTracerRegex 的各种信号使用场景
// ============================================================================

// Test 1: 基本信号声明
module test_signal_decl;
    // 各种信号声明
    logic a;                      // 1位
    logic [7:0] b;              // 8位向量
    logic [15:0] c;             // 16位
    reg [3:0] d;               // reg类型
    wire e;                     // wire类型
    
    // 赋值
    always_ff @(posedge clk) begin
        a <= 1'b0;
        b <= 8'h00;
    end
endmodule


// Test 2: 赋值表达式中的信号使用
module test_assignment_expr;
    logic clk;
    logic [7:0] a, b, c, result;
    
    // 右侧使用多个信号
    always_comb begin
        result = a + b;          // 使用 a, b
    end
    
    // 链式赋值
    always_comb begin
        c = a;
        b = c;
        result = a + b + c;       // 使用 a, b, c
    end
endmodule


// Test 3: 条件表达式中的信号使用
module test_condition_expr;
    logic clk;
    logic a, b, c, d;
    logic [1:0] sel;
    logic [7:0] data;
    
    // if条件
    always_comb begin
        if (a && b)              // 使用 a, b
            data = 8'h01;
        else if (c || d)         // 使用 c, d
            data = 8'h02;
        else if (sel == 2'b00)   // 使用 sel
            data = 8'h03;
        else
            data = 8'h00;
    end
    
    // case条件
    always_comb begin
        case (sel)
            2'b00: data = a ? 8'h01 : 8'h02;
            2'b01: data = b ? 8'h03 : 8'h04;
            2'b10: data = c ? 8'h05 : 8'h06;
            default: data = 8'h00;
        endcase
    end
endmodule


// Test 4: 时钟和复位事件中的信号
module test_clock_reset_events;
    logic clk;
    logic clk1, clk2;
    logic rst_n, rst_n1, rst_n2;
    logic [7:0] reg1, reg2, reg3;
    
    // 多时钟
    always_ff @(posedge clk1) begin
        reg1 <= reg1 + 1;
    end
    
    always_ff @(posedge clk2) begin
        reg2 <= reg2 + 1;
    end
    
    // 多复位
    always_ff @(posedge clk or negedge rst_n1) begin
        if (!rst_n1)
            reg1 <= 8'h00;
        else
            reg1 <= 8'h01;
    end
    
    always_ff @(posedge clk or negedge rst_n2) begin
        if (!rst_n2)
            reg2 <= 8'h00;
        else
            reg2 <= 8'h02;
    end
    
    // 组合事件
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            reg3 <= 8'h00;
        else
            reg3 <= 8'h03;
    end
endmodule


// Test 5: 位选择和切片
module test_bit_select;
    logic [15:0] data;
    logic [7:0] result1, result2;
    logic bit_val;
    
    always_comb begin
        result1 = data[7:0];      // 切片: 使用 data
        result2 = data[15:8];     // 切片: 使用 data
        bit_val = data[3];        // 位选择: 使用 data
    end
endmodule


// Test 6: 拼接表达式
module test_concatenation;
    logic [3:0] a, b;
    logic [7:0] result;
    
    always_comb begin
        result = {a, b};          // 拼接: 使用 a, b
    end
endmodule


// Test 7: 移位操作
module test_shift_ops;
    logic [7:0] data;
    logic [2:0] shift;
    logic [7:0] result1, result2, result3;
    
    always_comb begin
        result1 = data << shift;     // 移位: 使用 data, shift
        result2 = data >> shift;
        result3 = {data, 1'b0};     // 拼接+移位
    end
endmodule


// Test 8: 三元表达式
module test_ternary;
    logic [7:0] a, b, c;
    logic sel;
    logic [7:0] result;
    
    always_comb begin
        result = sel ? a : b;         // 三元: 使用 sel, a, b
        result = a ? (b ? 8'h01 : 8'h02) : (c ? 8'h03 : 8'h04);  // 嵌套三元
    end
endmodule


// Test 9: 函数调用中的信号使用
module test_function_call;
    logic [7:0] a, b;
    logic result;
    
    function logic [7:0] calc_sum(input logic [7:0] x, y);
        return x + y;
    endfunction
    
    always_comb begin
        result = calc_sum(a, b);     // 函数调用: 使用 a, b
    end
endmodule


// Test 10: 操作符表达式
module test_operators;
    logic [7:0] a, b, c, d;
    logic [7:0] result;
    
    always_comb begin
        // 算术运算
        result = a + b;              // 加法: 使用 a, b
        result = a - b;              // 减法: 使用 a, b
        result = a * b;              // 乘法: 使用 a, b
        result = a / b;              // 除法: 使用 a, b
        
        // 比较运算
        result = (a > b) ? 8'h01 : 8'h00;   // 大于: 使用 a, b
        result = (a < b) ? 8'h01 : 8'h00;   // 小于: 使用 a, b
        result = (a == b) ? 8'h01 : 8'h00;  // 等于: 使用 a, b
        
        // 逻辑运算
        result = (a && b) ? 8'h01 : 8'h00;   // 逻辑与: 使用 a, b
        result = (a || b) ? 8'h01 : 8'h00;   // 逻辑或: 使用 a, b
        result = !a;                            // 逻辑非: 使用 a
        
        // 位运算
        result = a & b;              // 与: 使用 a, b
        result = a | b;              // 或: 使用 a, b
        result = a ^ b;              // 异或: 使用 a, b
        result = ~a;                            // 非: 使用 a
    end
endmodule
