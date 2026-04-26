// ============================================================================
// FanoutAnalyzer 测试用例 - 验证扇出分析功能
// ============================================================================

// Test 1: 高扇出信号 - 时钟
module test_fanout_clk;
    logic clk;
    logic [7:0] reg0, reg1, reg2, reg3, reg4;
    
    always_ff @(posedge clk) begin
        reg0 <= 8'h00;
        reg1 <= 8'h01;
        reg2 <= 8'h02;
        reg3 <= 8'h03;
        reg4 <= 8'h04;
    end
endmodule

// Test 2: 高扇出信号 - 复位
module test_fanout_rst;
    logic rst_n;
    logic [7:0] reg0, reg1, reg2, reg3;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            reg0 <= 8'h00;
            reg1 <= 8'h00;
            reg2 <= 8'h00;
            reg3 <= 8'h00;
        end else begin
            reg0 <= reg0 + 1;
            reg1 <= reg1 + 1;
            reg2 <= reg2 + 1;
            reg3 <= reg3 + 1;
        end
    end
endmodule

// Test 3: 中等扇出信号
module test_fanout_medium;
    logic [7:0] enable;
    logic [7:0] out0, out1, out2;
    
    assign out0 = enable & 8'h01;
    assign out1 = enable & 8'h02;
    assign out2 = enable & 8'h04;
endmodule

// Test 4: 低扇出信号
module test_fanout_low;
    logic [7:0] a, b, c;
    logic [7:0] result;
    
    assign result = a + b + c;
endmodule

// Test 5: 单扇出信号
module test_fanout_single;
    logic [7:0] single_in;
    logic [7:0] single_out;
    
    assign single_out = single_in + 1;
endmodule

// Test 6: 零扇出信号 (未使用)
module test_fanout_zero;
    logic [7:0] unused_sig;
    
    assign unused_sig = 8'hAA;
endmodule

// Test 7: 多级扇出追溯
module test_fanout_multi_level;
    logic [7:0] root;
    logic [7:0] level1_a, level1_b;
    logic [7:0] level2_a, level2_b, level2_c;
    
    assign level1_a = root + 1;
    assign level1_b = root + 2;
    
    assign level2_a = level1_a + 1;
    assign level2_b = level1_b + 1;
    assign level2_c = level1_a + level1_b;
endmodule

// Test 8: 条件扇出
module test_fanout_conditional;
    logic [7:0] data;
    logic sel;
    logic [7:0] out0, out1;
    
    assign out0 = sel ? data : 8'h00;
    assign out1 = data & 8'hFF;
endmodule

// Test 9: 广播扇出
module test_fanout_broadcast;
    logic [7:0] broadcast;
    logic [7:0] targets [0:7];
    
    genvar i;
    for (i = 0; i < 8; i++) begin : gen_bcast
        assign targets[i] = broadcast;
    end
endmodule

// Test 10: 跨模块扇出
module test_fanout_cross;
    logic clk;
    logic [7:0] parent_sig;
    
    fanout_child inst0 (.clk(clk), .sig(parent_sig));
    fanout_child inst1 (.clk(clk), .sig(parent_sig));
    fanout_child inst2 (.clk(clk), .sig(parent_sig));
endmodule

module fanout_child (
    input logic clk,
    input logic [7:0] sig
);
    logic [7:0] reg_sig;
    always_ff @(posedge clk)
        reg_sig <= sig;
endmodule

// Test 11: 链式扇出
module test_fanout_chain;
    logic [7:0] src;
    logic [7:0] chain [0:9];
    
    assign chain[0] = src;
    genvar i;
    for (i = 1; i < 10; i++) begin : gen_chain
        assign chain[i] = chain[i-1] + 1;
    end
endmodule

// Test 12: 扇出反馈
module test_fanout_feedback;
    logic clk;
    logic [7:0] counter;
    
    always_ff @(posedge clk)
        counter <= counter + 1;
endmodule

// Test 13: 不同位宽扇出
module test_fanout_width;
    logic [31:0] wide;
    logic [7:0] byte0, byte1, byte2, byte3;
    
    assign byte0 = wide[7:0];
    assign byte1 = wide[15:8];
    assign byte2 = wide[23:16];
    assign byte3 = wide[31:24];
endmodule

// Test 14: 三元表达式扇出
module test_fanout_ternary;
    logic [7:0] a, b;
    logic sel;
    logic [7:0] out;
    
    assign out = sel ? a : b;  // out扇出a和b
endmodule

// Test 15: 移位扇出
module test_fanout_shift;
    logic [7:0] data;
    logic [2:0] shamt;
    logic [7:0] out0, out1, out2;
    
    assign out0 = data << shamt;
    assign out1 = data >> shamt;
    assign out2 = data << 2;
endmodule
