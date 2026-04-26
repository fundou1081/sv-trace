// ============================================================================
// LoadTracer 测试用例 - 验证信号负载追踪功能
// ============================================================================

// Test 1: always_ff中的负载 (寄存器)
module test_load_always_ff;
    logic clk;
    logic [7:0] d, q;
    
    always_ff @(posedge clk)
        q <= d;  // q被d负载
endmodule

// Test 2: always_comb中的负载 (组合逻辑)
module test_load_always_comb;
    logic [7:0] a, b, result;
    
    always_comb begin
        result = a + b;  // result被a和b负载
    end
endmodule

// Test 3: 多个信号被同一信号负载
module test_load_multi;
    logic [7:0] a;
    logic [7:0] b, c, d;
    
    assign b = a;
    assign c = a + 1;
    assign d = a + 2;
endmodule

// Test 4: 级联负载 (A->B->C)
module test_load_cascade;
    logic [7:0] a, b, c;
    
    assign b = a + 1;  // b负载a
    assign c = b + 1;  // c负载b
endmodule

// Test 5: 条件负载
module test_load_conditional;
    logic [7:0] a, b, sel;
    logic [7:0] result;
    
    assign result = sel ? a : b;  // result负载a或b
endmodule

// Test 6: 复选负载
module test_load_multiplexed;
    logic [7:0] in0, in1, in2, in3;
    logic [1:0] sel;
    logic [7:0] out;
    
    always_comb begin
        case (sel)
            2'd0: out = in0;
            2'd1: out = in1;
            2'd2: out = in2;
            default: out = in3;
        endcase
    end
endmodule

// Test 7: 移位操作负载
module test_load_shift;
    logic [7:0] data;
    logic [2:0] shamt;
    logic [7:0] shifted;
    
    assign shifted = data << shamt;
endmodule

// Test 8: 归约操作负载
module test_load_reduction;
    logic [7:0] data;
    logic parity;
    
    assign parity = ^data;  // parity负载data所有位
endmodule

// Test 9: generate块中的负载
module test_load_generate;
    logic clk;
    logic [7:0] out [0:3];
    
    genvar i;
    generate
        for (i = 0; i < 4; i++) begin : gen_load
            always_ff @(posedge clk)
                out[i] <= 8'(i);
        end
    endgenerate
endmodule

// Test 10: 跨模块端口负载
module test_load_cross_port;
    logic clk;
    logic [7:0] parent_sig;
    
    child_load u_child (.clk(clk), .sig(parent_sig));
endmodule

module child_load (
    input  logic clk,
    input  logic [7:0] sig
);
    logic [7:0] reg_sig;
    
    always_ff @(posedge clk)
        reg_sig <= sig;  // reg_sig负载sig
endmodule

// Test 11: 阻塞vs非阻塞负载
module test_load_blocking;
    logic clk;
    logic [7:0] a, b, c;
    
    always_ff @(posedge clk) begin
        b <= a;  // 非阻塞
    end
    
    always_comb begin
        c = a;  // 阻塞
    end
endmodule

// Test 12: 广播负载 (一驱动多)
module test_load_broadcast;
    logic [7:0] data;
    logic [7:0] out1, out2, out3, out4;
    
    assign out1 = data;
    assign out2 = data;
    assign out3 = data;
    assign out4 = data;
endmodule

// Test 13: always_latch负载
module test_load_latch;
    logic enable;
    logic [7:0] data_in, latch_out;
    
    always_latch begin
        if (enable)
            latch_out = data_in;
    end
endmodule

// Test 14: 函数调用的负载
module test_load_function;
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

// Test 15: 位选择作为负载
module test_load_bitselect;
    logic [7:0] data;
    logic bit0, bit7;
    
    assign bit0 = data[0];
    assign bit7 = data[7];
endmodule

// Test 16: 部分选择作为负载
module test_load_partselect;
    logic [15:0] data;
    logic [7:0] low, high;
    
    assign low = data[7:0];
    assign high = data[15:8];
endmodule

// Test 17: 未连接的负载 (悬空)
module test_load_dangling;
    logic clk;
    logic [7:0] data;
    logic [7:0] unused;
    
    always_ff @(posedge clk)
        unused <= data;  // unused被data负载，但未使用
endmodule

// Test 18: 三元表达式的负载
module test_load_ternary;
    logic [7:0] a, b;
    logic sel;
    logic [7:0] out;
    
    assign out = sel ? a : b;  // out负载a和b
endmodule
