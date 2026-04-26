// ============================================================================
// DataFlowTracer 底层功能测试
// 测试数据流分析的各种场景
// ============================================================================

// Test 1: 简单数据流 A -> B -> C
module dataflow_simple;
    logic clk;
    logic [7:0] a, b, c;
    
    always_ff @(posedge clk) begin
        b <= a;      // A -> B
        c <= b;      // B -> C
    end
endmodule


// Test 2: 多源数据流 A,B -> C
module dataflow_multi_source;
    logic clk;
    logic [7:0] a, b, c, result;
    
    always_ff @(posedge clk) begin
        c <= a + b;  // A,B -> C
        result <= c;  // C -> Result
    end
endmodule


// Test 3: 分支数据流 A -> B, A -> C
module dataflow_branch;
    logic clk;
    logic [7:0] a, b, c;
    logic sel;
    
    always_ff @(posedge clk) begin
        b <= a;      // A -> B
        c <= a;      // A -> C
    end
endmodule


// Test 4: 合并数据流 A -> C, B -> C
module dataflow_merge;
    logic clk;
    logic [7:0] a, b, c;
    
    always_ff @(posedge clk) begin
        c <= a;      // A -> C
        // B也驱动C? 如果是会产生多驱动
    end
endmodule


// Test 5: 反馈数据流 (有环)
module dataflow_feedback;
    logic clk;
    logic [7:0] data_in, data_out, feedback;
    
    always_ff @(posedge clk) begin
        feedback <= data_out + 1;  // data_out -> feedback
        data_out <= data_in + feedback;  // data_in,feedback -> data_out
    end
endmodule


// Test 6: 复杂表达式数据流
module dataflow_complex;
    logic clk;
    logic [7:0] a, b, c, d, result;
    
    always_ff @(posedge clk) begin
        result <= (a + b) * c - d;  // A,B,C,D -> Result
    end
endmodule


// Test 7: 条件数据流
module dataflow_conditional;
    logic clk;
    logic [7:0] a, b, c, result;
    logic sel;
    
    always_ff @(posedge clk) begin
        if (sel)
            result <= a + b;  // A,B -> Result (条件)
        else
            result <= c;       // C -> Result (条件)
    end
endmodule


// Test 8: 多级流水线数据流
module dataflow_pipeline;
    logic clk;
    logic [7:0] stage0, stage1, stage2, stage3, stage4;
    
    always_ff @(posedge clk) begin
        stage1 <= stage0 + 1;  // Stage0 -> Stage1
        stage2 <= stage1 + 1;  // Stage1 -> Stage2
        stage3 <= stage2 + 1;  // Stage2 -> Stage3
        stage4 <= stage3 + 1;  // Stage3 -> Stage4
    end
endmodule


// Test 9: 选择器数据流
module dataflow_mux;
    logic clk;
    logic [7:0] data0, data1, data2, data3;
    logic [1:0] sel;
    logic [7:0] result;
    
    always_comb begin
        case (sel)
            2'b00: result = data0;
            2'b01: result = data1;
            2'b10: result = data2;
            2'b11: result = data3;
        endcase
    end
endmodule


// Test 10: 算术链数据流
module dataflow_arith_chain;
    logic clk;
    logic [15:0] a, b, c, d;
    logic [31:0] result;
    
    always_comb begin
        result = (a * b) + (c * d);  // A,B,C,D -> Result
    end
endmodule
