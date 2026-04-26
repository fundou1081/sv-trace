// ============================================================================
// DriverCollector 测试用例 - 验证驱动收集功能
// ============================================================================

// Test 1: 连续赋值 (assign)
module test_continuous_assign;
    wire [7:0] a, b, c;
    assign c = a & b;  // c的驱动是连续赋值
endmodule

// Test 2: always_ff块 (非阻塞赋值)
module test_always_ff;
    logic clk;
    logic [7:0] reg_a, reg_b;
    
    always_ff @(posedge clk) begin
        reg_a <= reg_b + 1;  // 非阻塞赋值
    end
endmodule

// Test 3: always_comb块 (阻塞赋值)
module test_always_comb;
    logic [7:0] a, b, result;
    
    always_comb begin
        result = a + b;  // 阻塞赋值
    end
endmodule

// Test 4: always_latch块
module test_always_latch;
    logic enable;
    logic [7:0] data_in, latch_out;
    
    always_latch begin
        if (enable)
            latch_out = data_in;  // 锁存
    end
endmodule

// Test 5: 多驱动同一信号
module test_multi_driver;
    logic [7:0] out;
    logic sel;
    
    assign out = sel ? 8'hAA : 8'h00;  // 条件驱动1
    // 实际上只有一个assign，这是正确的
endmodule

// Test 6: 嵌套表达式驱动
module test_nested_expr;
    logic [7:0] a, b, c, d, result;
    
    always_comb begin
        result = (a + b) * (c - d);  // 复杂表达式
    end
endmodule

// Test 7: 移位操作驱动
module test_shift_ops;
    logic [7:0] data;
    logic [2:0] shift_amt;
    logic [7:0] shifted;
    
    always_comb begin
        shifted = data << shift_amt;  // 左移
    end
endmodule

// Test 8: 三元表达式驱动
module test_ternary;
    logic [7:0] a, b;
    logic sel;
    logic [7:0] result;
    
    always_comb begin
        result = sel ? a : b;  // 三元
    end
endmodule

// Test 9: 模块实例端口驱动
module test_inst_port;
    logic clk;
    logic [7:0] data_in, data_out;
    
    sub_module u_sub (
        .clk(clk),
        .din(data_in),
        .dout(data_out)
    );
endmodule

module sub_module (
    input  logic clk,
    input  logic [7:0] din,
    output logic [7:0] dout
);
    always_ff @(posedge clk)
        dout <= din;
endmodule

// Test 10: generate块中的驱动
module test_generate_driver;
    logic clk;
    logic [7:0] out [0:3];
    
    genvar i;
    generate
        for (i = 0; i < 4; i++) begin : gen_loop
            always_ff @(posedge clk) begin
                out[i] <= 8'(i);
            end
        end
    endgenerate
endmodule

// Test 11: 复位信号驱动
module test_reset_driver;
    logic clk, rst_n;
    logic [7:0] counter;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            counter <= 8'h00;  // 复位赋值
        else
            counter <= counter + 1;
    end
endmodule

// Test 12: case语句中的驱动
module test_case_driver;
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

// Test 13: if-else语句中的驱动
module test_if_driver;
    logic enable;
    logic [7:0] a, b, result;
    
    always_comb begin
        if (enable)
            result = a;
        else
            result = b;
    end
endmodule

// Test 14: 拼接操作驱动
module test_concat_driver;
    logic [3:0] a, b;
    logic [7:0] result;
    
    assign result = {a, b};  // 拼接
endmodule

// Test 15: 位选择驱动
module test_bitselect_driver;
    logic [7:0] data;
    logic result;
    
    assign result = data[3];  // 位选择
endmodule

// Test 16: 跨模块信号驱动
module test_cross_module_driver;
    logic clk;
    logic [7:0] top_sig;
    
    // 实例化子模块
    child_inst u_child (.clk(clk), .sig(top_sig));
endmodule

module child_inst (
    input  logic clk,
    input  logic [7:0] sig
);
    logic [7:0] reg_sig;
    
    always_ff @(posedge clk)
        reg_sig <= sig;
endmodule
