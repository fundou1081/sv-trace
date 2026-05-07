// ============================================================================
// Lint 测试用例 - 代码风格问题
// ============================================================================

// 问题1: Case 无 default
module case_no_default(
    input clk,
    input [1:0] sel,
    output [7:0] out
);
    always_ff @(posedge clk) begin
        case (sel)
            2'b00: out <= 8'h00;
            2'b01: out <= 8'hFF;
            // 缺少 default!
        endcase
    end
endmodule

// 问题2: Latch 推断 (组合逻辑中的 if 不完整)
module latch_inferred(
    input clk,
    input enable,
    input [7:0] data,
    output [7:0] out
);
    always_ff @(posedge clk) begin
        if (enable)  // 没有 else!
            out <= data;
    end
endmodule

// 问题3: 未使用的信号
module unused_signals(
    input clk,
    input a, b, c,
    output reg y
);
    wire temp1, temp2;
    
    assign temp1 = a & b;
    assign temp2 = b & c;  // temp2 未使用
    assign y = temp1;
endmodule

// 问题4: 未连接的输出
module unconnected_output(
    input clk,
    input [7:0] data_in,
    output [7:0] data_out
    // valid 信号未连接
);
    always_ff @(posedge clk) begin
        data_out <= data_in;
    end
endmodule

// 问题5: 组合逻辑环路 (反馈)
module comb_loop(
    input a,
    input b,
    output y
);
    wire y;
    assign y = (a & b) | y;  // 问题: y 依赖自身
endmodule

// OK: 正确的代码
module good_style(
    input clk,
    input [1:0] sel,
    input [7:0] data,
    output reg [7:0] out
);
    always_ff @(posedge clk) begin
        case (sel)
            2'b00: out <= 8'h00;
            2'b01: out <= data;
            2'b10: out <= 8'hFF;
            default: out <= 8'h00;  // 有 default
        endcase
    end
endmodule
