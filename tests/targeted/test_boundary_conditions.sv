// ============================================================================
// 边界条件测试
// ============================================================================

// Test 1: 空模块
module empty_module;
    // 没有任何内容
endmodule


// Test 2: 只有端口的模块
module port_only_module (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    assign data_out = data_in;
endmodule


// Test 3: 超大位宽
module huge_bitwidth (
    input  logic clk,
    input  logic rst_n,
    input  logic [8191:0] huge_data_in,
    output logic [8191:0] huge_data_out
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            huge_data_out <= 8192'b0;
        else
            huge_data_out <= huge_data_in;
    end
endmodule


// Test 4: 超多信号
module many_signals (
    input  logic clk,
    input  logic rst_n
);
    genvar i;
    generate
        for (i = 0; i < 1000; i = i + 1) begin : gen_signals
            logic [7:0] sig;
            always_ff @(posedge clk) begin
                sig <= sig + 1;
            end
        end
    endgenerate
endmodule


// Test 5: 超多实例化
module small_unit (
    input  logic clk,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    always_ff @(posedge clk) begin
        data_out <= data_in + 1;
    end
endmodule

module many_instances (
    input  logic clk,
    input  logic rst_n
);
    genvar i;
    generate
        for (i = 0; i < 100; i = i + 1) begin : gen_inst
            logic [7:0] data;
            small_unit u_unit (
                .clk(clk),
                .data_in(data),
                .data_out(data)
            );
        end
    endgenerate
endmodule


// Test 6: 深层嵌套
module deep_nesting (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] level0,
    output logic [7:0] level10
);
    logic [7:0] level1, level2, level3, level4, level5;
    logic [7:0] level6, level7, level8, level9;
    
    always_ff @(posedge clk) begin
        level1 <= level0 + 1;
        level2 <= level1 + 1;
        level3 <= level2 + 1;
        level4 <= level3 + 1;
        level5 <= level4 + 1;
        level6 <= level5 + 1;
        level7 <= level6 + 1;
        level8 <= level7 + 1;
        level9 <= level8 + 1;
        level10 <= level9 + 1;
    end
endmodule


// Test 7: 非常深的always块嵌套
module deep_always_nesting (
    input  logic clk,
    input  logic rst_n,
    input  logic a, b, c, d, e, f, g, h,
    output logic result
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            result <= 1'b0;
        end else if (a) begin
            if (b) begin
                if (c) begin
                    if (d) begin
                        if (e) begin
                            if (f) begin
                                if (g) begin
                                    if (h) begin
                                        result <= 1'b1;
                                    end else begin
                                        result <= 1'b0;
                                    end
                                end else begin
                                    result <= 1'b0;
                                end
                            end else begin
                                result <= 1'b0;
                            end
                        end else begin
                            result <= 1'b0;
                        end
                    end else begin
                        result <= 1'b0;
                    end
                end else begin
                    result <= 1'b0;
                end
            end else begin
                result <= 1'b0;
            end
        end else begin
            result <= 1'b0;
        end
    end
endmodule


// Test 8: 单信号模块
module single_signal_module (
    input  logic clk,
    output logic single_bit
);
    assign single_bit = clk;
endmodule


// Test 9: 零宽度信号
module zero_width (
    input  logic clk,
    input  logic rst_n
);
    logic [`0:0] zero_width_sig;  // 0位宽
    always_ff @(posedge clk) begin
        zero_width_sig <= 1'b0;
    end
endmodule


// Test 10: 负数索引信号
module negative_index (
    input  logic clk,
    input  logic rst_n
);
    logic [0:7] reverse_vec;  // 反向索引
    logic bit_0, bit_7;
    
    always_ff @(posedge clk) begin
        bit_0 <= reverse_vec[0];
        bit_7 <= reverse_vec[7];
    end
endmodule


// Test 11: 未连接的端口
module unconnected_ports (
    input  logic clk,
    input  logic rst_n,
    input  logic a,  // 未使用
    input  logic b,  // 未使用
    output logic out
);
    logic unused1, unused2;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            out <= 1'b0;
        end else begin
            out <= 1'b1;
        end
    end
endmodule


// Test 12: 多驱动(危险)
module multi_driver_bad (
    input  logic clk,
    input  logic a,
    input  logic b,
    output logic y  // 多驱动!
);
    always_ff @(posedge clk) begin
        y <= a;  // 驱动1
    end
    
    always_ff @(posedge clk) begin
        y <= b;  // 驱动2 - 危险!
    end
endmodule
