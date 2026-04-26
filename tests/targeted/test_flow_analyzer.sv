// ============================================================================
// FlowAnalyzer 测试用例 - 数据流分析
// ============================================================================

// Test 1: 简单数据流
module test_flow_simple;
    logic [7:0] a, b, result;
    
    assign result = a + b;
endmodule

// Test 2: 多级数据流
module test_flow_multi;
    logic [7:0] a, b, c, d, result;
    
    assign b = a + 1;
    assign c = b + 1;
    assign d = c + 1;
    assign result = d + 1;
endmodule

// Test 3: 反馈数据流
module test_flow_feedback;
    logic clk;
    logic [7:0] counter;
    
    always_ff @(posedge clk)
        counter <= counter + 1;
endmodule

// Test 4: 条件数据流
module test_flow_cond;
    logic [7:0] a, sel, result;
    
    assign result = sel ? a : 8'h00;
endmodule

// Test 5: 双向数据流
module test_flow_bidir;
    logic [7:0] data;
    
    assign data = 8'h00;
endmodule

// Test 6: 跨模块数据流
module test_flow_cross;
    logic clk;
    logic [7:0] sig;
    
    flow_child u_child (.sig(sig));
endmodule

module flow_child (
    input  logic [7:0] sig
);
    logic [7:0] reg_sig;
    
    always_ff @(posedge clk)
        reg_sig <= sig;
endmodule

// Test 7: 流水线数据流
module test_flow_pipe;
    logic clk;
    logic [7:0] s1, s2, s3;
    
    always_ff @(posedge clk) begin
        s1 <= 8'h00;
        s2 <= s1;
        s3 <= s2;
    end
endmodule

// Test 8: 分支数据流
module test_flow_branch;
    logic [7:0] a;
    logic [7:0] out0, out1, out2;
    
    assign out0 = a + 1;
    assign out1 = a + 2;
    assign out2 = a + 3;
endmodule

// Test 9: 合并数据流
module test_flow_merge;
    logic [7:0] a, b, c, result;
    
    assign result = a + b + c;
endmodule

// Test 10: 选择数据流
module test_flow_select;
    logic [7:0] in0, in1, sel, out;
    
    assign out = sel ? in0 : in1;
endmodule

// Test 11: 多路选择数据流
module test_flow_mux;
    logic [7:0] in0, in1, in2, in3;
    logic [1:0] sel;
    logic [7:0] out;
    
    assign out = (sel == 2'b00) ? in0 :
             (sel == 2'b01) ? in1 :
             (sel == 2'b10) ? in2 : in3;
endmodule

// Test 12: 循环数据流
module test_flow_loop;
    logic [7:0] data [0:3];
    
    assign data[0] = 8'h00;
    assign data[1] = data[0] + 1;
    assign data[2] = data[1] + 1;
    assign data[3] = data[2] + 1;
endmodule

// Test 13: 深度嵌套
module test_flow_deep;
    logic [7:0] a, b, c, d, e, result;
    
    assign b = (a + 1);
    assign c = (a + b);
    assign d = (a + b + c);
    assign e = (a + b + c + d);
    assign result = e;
endmodule

// Test 14: 同步数据流
module test_flow_sync;
    logic clk;
    logic [7:0] in, out;
    
    always_ff @(posedge clk)
        out <= in + 1;
endmodule

// Test 15: 异步数据流
module test_flow_async;
    logic [7:0] a, b;
    
    assign b = a + 1;
endmodule

// Test 16: 多时钟数据流
module test_flow_multiclock;
    logic clk1, clk2;
    logic [7:0] r1, r2;
    
    always_ff @(posedge clk1)
        r1 <= 8'h01;
    
    always_ff @(posedge clk2)
        r2 <= r1;
endmodule

// Test 17: 使能数据流
module test_flow_enable;
    logic clk, enable;
    logic [7:0] data, out;
    
    always_ff @(posedge clk) begin
        if (enable)
            out <= data + 1;
    end
endmodule

// Test 18: 握手数据流
module test_flow_handshake;
    logic clk, valid;
    logic [7:0] data, out;
    logic ready;
    
    always_ff @(posedge clk) begin
        if (valid && ready)
            out <= data;
    end
endmodule

// Test 19: FIFO数据流
module test_flow_fifo;
    logic clk;
    logic [7:0] din, dout;
    logic wr_en, rd_en;
    logic full, empty;
    
    always_ff @(posedge clk) begin
        if (wr_en && !full)
            dout <= din;
    end
endmodule

// Test 20: 状态机数据流
module test_flow_fsm;
    logic clk, rst_n;
    logic [1:0] state;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= 2'b00;
        else
            state <= state + 1;
    end
endmodule
