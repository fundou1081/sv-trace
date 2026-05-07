// ============================================================================
// Lint 测试用例 - 20个问题语法组合
// ============================================================================

// LINT-01: Case 无 default
module lint_01_case_no_default(
    input clk,
    input [1:0] sel,
    output [7:0] out
);
    always_ff @(posedge clk)
        case (sel)
            2'b00: out <= 8'h00;
            2'b01: out <= 8'hFF;
            // 无 default
        endcase
endmodule

// LINT-02: Case 全部覆盖 (OK)
module lint_02_case_with_default(
    input clk,
    input [1:0] sel,
    output [7:0] out
);
    always_ff @(posedge clk)
        case (sel)
            2'b00: out <= 8'h00;
            2'b01: out <= 8'hFF;
            default: out <= 8'hAA;
        endcase
endmodule

// LINT-03: Latch 推断 (if 无 else)
module lint_03_latch_if_no_else(
    input clk, enable,
    input [7:0] data,
    output [7:0] out
);
    always_ff @(posedge clk)
        if (enable)
            out <= data;
        // 无 else 分支 -> 推断 latch
endmodule

// LINT-04: 正确使用 always_ff
module lint_04_correct_ff(
    input clk, enable,
    input [7:0] data,
    output [7:0] out
);
    always_ff @(posedge clk)
        if (enable)
            out <= data;
        else
            out <= 8'h00;
endmodule

// LINT-05: 组合逻辑环路
module lint_05_comb_loop(
    input a, b,
    output y
);
    assign y = (a ^ b) ^ y;  // y 依赖自身
endmodule

// LINT-06: 无环路组合逻辑
module lint_06_no_comb_loop(
    input a, b, c,
    output y
);
    assign y = (a ^ b) ^ c;
endmodule

// LINT-07: 未使用的 wire
module lint_07_unused_wire(
    input a, b,
    output y
);
    wire temp1, temp2;  // temp2 未使用
    assign temp1 = a & b;
    assign y = temp1;
endmodule

// LINT-08: 所有信号都使用 (OK)
module lint_08_all_used(
    input a, b,
    output y, z
);
    assign y = a & b;
    assign z = a | b;
endmodule

// LINT-09: 未连接的输出
module lint_09_unconnected_output(
    input clk,
    input [7:0] data_in,
    output [7:0] data_out
    // valid 信号未声明
);
    always_ff @(posedge clk)
        data_out <= data_in;
endmodule

// LINT-10: 所有输出连接 (OK)
module lint_10_all_connected(
    input clk,
    input [7:0] data_in,
    output [7:0] data_out,
    output valid
);
    always_ff @(posedge clk) begin
        data_out <= data_in;
        valid <= 1'b1;
    end
endmodule

// LINT-11: 异步复位在时钟沿
module lint_11_bad_reset_pos;
    logic clk, rst;
    logic [7:0] data;
    always_ff @(posedge clk, posedge rst)  // 问题: 异步复位不应该在时钟沿
        if (rst)
            data <= 8'h00;
        else
            data <= data + 1;
endmodule

// LINT-12: 正确的异步复位
module lint_12_good_async_reset;
    logic clk, rst_n;
    logic [7:0] data;
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n)
            data <= 8'h00;
        else
            data <= data + 1;
endmodule

// LINT-13: 多驱动
module lint_13_multi_driver(
    input clk,
    input [7:0] a, b,
    output [7:0] y
);
    always_ff @(posedge clk)
        y <= a;
    always_ff @(posedge clk)
        y <= b;  // 多驱动
endmodule

// LINT-14: 单驱动 (OK)
module lint_14_single_driver(
    input clk,
    input [7:0] a, b, sel,
    output [7:0] y
);
    always_ff @(posedge clk)
        if (sel)
            y <= a;
        else
            y <= b;
endmodule

// LINT-15: X 赋值
module lint_15_x_assignment(
    input clk,
    output [7:0] data
);
    always_ff @(posedge clk)
        data <= 8'bx;  // X 赋值
endmodule

// LINT-16: 正常赋值
module lint_16_normal_assign(
    input clk,
    output [7:0] data
);
    always_ff @(posedge clk)
        data <= 8'h00;
endmodule

// LINT-17: partial case 无 default
module lint_17_partial_case(
    input clk,
    input [3:0] sel,
    output [7:0] out
);
    always_ff @(posedge clk)
        case (sel)
            4'b0001: out <= 8'h01;
            4'b0010: out <= 8'h02;
            // 只有 2 个分支，但 sel 是 4bit
        endcase
endmodule

// LINT-18: 完整 case
module lint_18_full_case(
    input clk,
    input [3:0] sel,
    output [7:0] out
);
    always_ff @(posedge clk)
        case (sel)
            4'b0001: out <= 8'h01;
            4'b0010: out <= 8'h02;
            4'b0100: out <= 8'h04;
            4'b1000: out <= 8'h08;
            default: out <= 8'h00;
        endcase
endmodule

// LINT-19: generate 内多个实例同名
module lint_19_gen_same_name;
endmodule
module lint_19_top;
    generate
        genvar i;
        for (i = 0; i < 2; i = i + 1) begin : same_name
            // 注意: 相同名称在不同 scope 中是允许的
            lint_19_gen_same_name u();
        end
    endgenerate
endmodule

// LINT-20: 阻塞/非阻塞混用
module lint_20_mixed_blocking(
    input clk,
    input [7:0] a, b,
    output [7:0] y
);
    always_ff @(posedge clk) begin
        y = a;      // 阻塞赋值在 always_ff 中
        y = b;      // 再次赋值
    end
endmodule
