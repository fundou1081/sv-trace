// ============================================================================
// DriverTracer 测试用例 - 20个语法组合
// ============================================================================

// 1. 基本 assign 驱动
module driver_01_assign_basic;
    wire [7:0] a;
    assign a = 8'hFF;
endmodule

// 2. 多重 assign
module driver_02_assign_multiple;
    wire [7:0] a, b, c;
    assign a = 8'h00;
    assign b = a + 1;
    assign c = b & 8'h0F;
endmodule

// 3. always_ff posedge 时钟
module driver_03_ff_posedge;
    logic clk;
    logic [7:0] data;
    always_ff @(posedge clk) begin
        data <= data + 1;
    end
endmodule

// 4. always_ff negedge 时钟
module driver_04_ff_negedge;
    logic clk;
    logic [7:0] data;
    always_ff @(negedge clk) begin
        data <= data + 1;
    end
endmodule

// 5. always_ff 多时钟沿
module driver_05_ff_multi_clock;
    logic clk_a, clk_b;
    logic [7:0] data_a, data_b;
    always_ff @(posedge clk_a or posedge clk_b) begin
        if (clk_a) data_a <= data_a + 1;
        if (clk_b) data_b <= data_b + 1;
    end
endmodule

// 6. always_ff 带异步复位
module driver_06_ff_async_reset;
    logic clk, rst_n;
    logic [7:0] data;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data <= 8'h00;
        else
            data <= data + 1;
    end
endmodule

// 7. always_ff 带同步复位
module driver_07_ff_sync_reset;
    logic clk, rst;
    logic [7:0] data;
    always_ff @(posedge clk) begin
        if (rst)
            data <= 8'h00;
        else
            data <= data + 1;
    end
endmodule

// 8. always_comb 基本
module driver_08_comb_basic;
    logic [7:0] a, b, c;
    always_comb begin
        c = a + b;
    end
endmodule

// 9. always_comb 多表达式
module driver_09_comb_multi_expr;
    logic [7:0] a, b, c, d, e;
    always_comb begin
        c = a + b;
        d = a - b;
        e = a & b;
    end
endmodule

// 10. always_latch
module driver_10_latch;
    logic clk, en;
    logic [7:0] data_in, data_out;
    always_latch begin
        if (en)
            data_out = data_in;
    end
endmodule

// 11. if-else 嵌套
module driver_11_if_nested;
    logic clk;
    logic [7:0] a, b, sel;
    logic [7:0] out;
    always_ff @(posedge clk) begin
        if (sel > 8'd10)
            out <= a;
        else if (sel > 8'd5)
            out <= b;
        else
            out <= 8'h00;
    end
endmodule

// 12. case 语句
module driver_12_case;
    logic clk;
    logic [1:0] sel;
    logic [7:0] out;
    always_ff @(posedge clk) begin
        case (sel)
            2'b00: out <= 8'h00;
            2'b01: out <= 8'hFF;
            2'b10: out <= 8'hAA;
            default: out <= 8'h00;
        endcase
    end
endmodule

// 13. casez 通配符
module driver_13_casez;
    logic clk;
    logic [3:0] sel;
    logic [7:0] out;
    always_ff @(posedge clk) begin
        casez (sel)
            4'b1???: out <= 8'hFF;
            4'b01??: out <= 8'hAA;
            default: out <= 8'h00;
        endcasez
    end
endmodule

// 14. casex x/z 通配符
module driver_14_casex;
    logic clk;
    logic [3:0] sel;
    logic [7:0] out;
    always_ff @(posedge clk) begin
        casex (sel)
            4'b1xxx: out <= 8'hFF;
            4'b0xxx: out <= 8'h00;
            default: out <= 8'hAA;
        endcasex
    end
endmodule

// 15. for 循环
module driver_15_for_loop;
    logic clk;
    logic [7:0] data [0:7];
    integer i;
    always_ff @(posedge clk) begin
        for (i = 0; i < 8; i = i + 1) begin
            data[i] <= data[i] + 1;
        end
    end
endmodule

// 16. generate if
module driver_16_gen_if #(
    parameter WIDTH = 8
)(
    input clk,
    input [WIDTH-1:0] in_data,
    output reg [WIDTH-1:0] out_data
);
    generate
        if (WIDTH > 8) begin : gen_big
            always_ff @(posedge clk)
                out_data <= in_data + 1;
        end else begin : gen_small
            always_ff @(posedge clk)
                out_data <= in_data + 2;
        end
    endgenerate
endmodule

// 17. generate for
module driver_17_gen_for #(
    parameter N = 4
)(
    input clk,
    input [7:0] data_in,
    output [7:0] data_out
);
    genvar i;
    wire [7:0] stages [0:N];
    
    assign stages[0] = data_in;
    
    generate
        for (i = 0; i < N; i = i + 1) begin : gen_stage
            always_ff @(posedge clk)
                stages[i+1] <= stages[i] + 1;
        end
    endgenerate
    
    assign data_out = stages[N];
endmodule

// 18. 阻塞赋值
module driver_18_blocking;
    logic clk;
    logic [7:0] a, b, c;
    always_ff @(posedge clk) begin
        a = b;      // 阻塞
        b = c;      // 阻塞
        c = a + 1;  // 阻塞
    end
endmodule

// 19. 非阻塞赋值
module driver_19_nonblocking;
    logic clk;
    logic [7:0] a, b, c;
    always_ff @(posedge clk) begin
        a <= b;      // 非阻塞
        b <= c;      // 非阻塞
        c <= a + 1;  // 非阻塞
    end
endmodule

// 20. 混合阻塞/非阻塞
module driver_20_mixed;
    logic clk;
    logic [7:0] a, b, c, d;
    always_ff @(posedge clk) begin
        a <= b + 1;      // 非阻塞
        b <= c;           // 非阻塞
        c = a + d;       // 阻塞
    end
endmodule
