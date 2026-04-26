// ============================================================================
// DataFlowTracer 测试用例 - 验证数据流分析功能
// ============================================================================

// Test 1: 简单数据流
module test_df_simple;
    logic [7:0] a, b, result;
    
    assign result = a + b;
endmodule

// Test 2: 流水线数据流
module test_df_pipeline;
    logic clk;
    logic [7:0] stage0, stage1, stage2, stage3;
    
    always_ff @(posedge clk) begin
        stage0 <= stage3 + 1;
        stage1 <= stage0;
        stage2 <= stage1;
        stage3 <= stage2;
    end
endmodule

// Test 3: 多路数据流
module test_df_mux;
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

// Test 4: 分支数据流
module test_df_branch;
    logic [7:0] a;
    logic [7:0] out0, out1, out2;
    
    assign out0 = a + 1;
    assign out1 = a + 2;
    assign out2 = a + 3;
endmodule

// Test 5: 合并数据流
module test_df_merge;
    logic [7:0] a, b, c, result;
    
    assign result = a + b + c;
endmodule

// Test 6: 反馈数据流
module test_df_feedback;
    logic clk;
    logic [7:0] counter;
    
    always_ff @(posedge clk)
        counter <= counter + 1;
endmodule

// Test 7: 复杂表达式数据流
module test_df_complex;
    logic [7:0] a, b, c, d, result;
    
    assign result = ((a + b) * (c - d)) & 8'hFF;
endmodule

// Test 8: 跨模块数据流
module test_df_cross;
    logic clk;
    logic [7:0] sig;
    
    df_child inst (.clk(clk), .sig(sig));
endmodule

module df_child (
    input  logic clk,
    input  logic [7:0] sig
);
    logic [7:0] reg_sig;
    
    always_ff @(posedge clk)
        reg_sig <= sig;
endmodule

// Test 9: 生成块数据流
module test_df_generate;
    logic clk;
    logic [7:0] out [0:3];
    
    genvar i;
    generate
        for (i = 0; i < 4; i++) begin : gen_df
            always_ff @(posedge clk)
                out[i] <= 8'(i);
        end
    endgenerate
endmodule

// Test 10: 移位数据流
module test_df_shift;
    logic [7:0] data;
    logic [2:0] shamt;
    logic [7:0] shifted;
    
    assign shifted = data << shamt;
endmodule

// Test 11: 加法器树数据流
module test_df_adder_tree;
    logic [7:0] a, b, c, d;
    logic [7:0] sum1, sum2, total;
    
    assign sum1 = a + b;
    assign sum2 = c + d;
    assign total = sum1 + sum2;
endmodule

// Test 12: 选择器数据流
module test_df_select;
    logic [7:0] a, b;
    logic sel;
    logic [7:0] result;
    
    assign result = sel ? a : b;
endmodule

// Test 13: 位选择数据流
module test_df_bitselect;
    logic [15:0] data;
    logic [7:0] low, high;
    
    assign low = data[7:0];
    assign high = data[15:8];
endmodule

// Test 14: 拼接数据流
module test_df_concat;
    logic [3:0] a, b;
    logic [7:0] result;
    
    assign result = {a, b};
endmodule

// Test 15: 三元链数据流
module test_df_ternary_chain;
    logic [7:0] a, b, c;
    logic [1:0] sel;
    logic [7:0] result;
    
    assign result = (sel == 2'd0) ? a :
                    (sel == 2'd1) ? b : c;
endmodule

// Test 16: 计数数据流
module test_df_counter;
    logic clk;
    logic [7:0] counter;
    
    always_ff @(posedge clk)
        counter <= counter + 1;
endmodule

// Test 17: 同步FIFO数据流
module test_df_fifo;
    logic clk;
    logic [7:0] din, dout;
    logic wr_en, rd_en;
    logic full, empty;
    
    always_ff @(posedge clk) begin
        if (wr_en && !full)
            dout <= din;
    end
endmodule

// Test 18: 状态机数据流
module test_df_fsm;
    logic clk, rst_n;
    logic [1:0] state, next;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= 2'b00;
        else
            state <= next;
    end
    
    always_comb begin
        case (state)
            2'b00: next = 2'b01;
            2'b01: next = 2'b10;
            2'b10: next = 2'b00;
            default: next = 2'b00;
        endcase
    end
endmodule
