// ============================================================================
// ConnectionTracer 测试用例 - 验证连接分析功能
// ============================================================================

// Test 1: 简单模块实例连接
module test_conn_simple;
    logic clk;
    logic [7:0] data_in, data_out;
    
    sub_conn u_sub (
        .clk(clk),
        .din(data_in),
        .dout(data_out)
    );
endmodule

module sub_conn (
    input  logic clk,
    input  logic [7:0] din,
    output logic [7:0] dout
);
    always_ff @(posedge clk)
        dout <= din;
endmodule

// Test 2: 多端口模块连接
module test_conn_multi_port;
    logic clk, rst, en;
    logic [7:0] a, b, c, out;
    
    multi_port u_mp (
        .clk(clk),
        .rst(rst),
        .en(en),
        .a(a),
        .b(b),
        .c(c),
        .out(out)
    );
endmodule

module multi_port (
    input  logic clk, rst, en,
    input  logic [7:0] a, b, c,
    output logic [7:0] out
);
    always_ff @(posedge clk)
        if (en)
            out <= a + b + c;
endmodule

// Test 3: 跨层次连接
module test_conn_hierarchy;
    logic clk;
    logic [7:0] sig;
    
    level1 u_l1 (.clk(clk), .sig(sig));
endmodule

module level1 (
    input  logic clk,
    input  logic [7:0] sig
);
    logic [7:0] reg_sig;
    level2 u_l2 (.clk(clk), .sig(reg_sig));
    
    always_ff @(posedge clk)
        reg_sig <= sig;
endmodule

module level2 (
    input  logic clk,
    input  logic [7:0] sig
);
    logic [7:0] reg_sig;
    always_ff @(posedge clk)
        reg_sig <= sig;
endmodule

// Test 4: 点对点连接
module test_conn_point2point;
    logic [7:0] src, dst;
    
    assign dst = src;
endmodule

// Test 5: 多驱动连接
module test_conn_multi_driver;
    logic [7:0] a, b, sel, out;
    
    assign out = sel ? a : b;
endmodule

// Test 6: 位选择连接
module test_conn_bitselect;
    logic [15:0] data;
    logic [7:0] byte0, byte1;
    
    assign byte0 = data[7:0];
    assign byte1 = data[15:8];
endmodule

// Test 7: 拼接连接
module test_conn_concat;
    logic [3:0] low, high;
    logic [7:0] combined;
    
    assign combined = {high, low};
endmodule

// Test 8: 未连接端口
module test_conn_unconnected;
    logic clk;
    logic [7:0] data;
    
    unconn_inst u_inst (.clk(clk), .data(data), .out());
endmodule

module unconn_inst (
    input  logic clk,
    input  logic [7:0] data,
    output logic [7:0] out
);
    always_ff @(posedge clk)
        out <= data;
endmodule

// Test 9: 带默认值端口连接
module test_conn_default;
    logic clk;
    logic [7:0] out;
    
    defconn_inst u_def (.clk(clk), .out(out));
endmodule

module defconn_inst (
    input  logic clk,
    input  logic [7:0] data = 8'h00,
    output logic [7:0] out
);
    always_ff @(posedge clk)
        out <= data;
endmodule

// Test 10: 数组端口连接
module test_conn_array_port;
    logic clk;
    logic [7:0] in_data [0:3];
    logic [7:0] out_data [0:3];
    
    genvar i;
    for (i = 0; i < 4; i++) begin : gen_arr
        arr_port u_arr (.clk(clk), .din(in_data[i]), .dout(out_data[i]));
    end
endmodule

module arr_port (
    input  logic clk,
    input  logic [7:0] din,
    output logic [7:0] dout
);
    always_ff @(posedge clk)
        dout <= din;
endmodule

// Test 11: 命名端口连接顺序无关
module test_conn_named;
    logic clk;
    logic [7:0] a, b, result;
    
    named_conn u_nc (
        .clk(clk),
        .a(a),
        .b(b),
        .result(result)
    );
endmodule

module named_conn (
    input  logic clk,
    input  logic [7:0] a, b,
    output logic [7:0] result
);
    always_ff @(posedge clk)
        result <= a + b;
endmodule

// Test 12: .* 隐式端口连接
module test_conn_implicit;
    logic clk;
    logic [7:0] in_sig, out_sig;
    
    implicit_conn u_ic (.*);
endmodule

module implicit_conn (
    input  logic clk,
    input  logic [7:0] in_sig,
    output logic [7:0] out_sig
);
    always_ff @(posedge clk)
        out_sig <= in_sig;
endmodule

// Test 13: 模块输出反馈
module test_conn_feedback;
    logic clk;
    logic [7:0] counter;
    
    counter_inst u_cnt (.clk(clk), .count(counter));
endmodule

module counter_inst (
    input  logic clk,
    output logic [7:0] count
);
    always_ff @(posedge clk)
        count <= count + 1;
endmodule

// Test 14: 参数化模块连接
module test_conn_param #(
    parameter WIDTH = 8
) (
    input  logic clk,
    input  logic [WIDTH-1:0] data,
    output logic [WIDTH-1:0] out
);
    always_ff @(posedge clk)
        out <= data;
endmodule

module test_conn_param_top;
    logic clk;
    logic [7:0] data8, out8;
    logic [15:0] data16, out16;
    
    param_inst #(.WIDTH(8)) u8 (.clk(clk), .data(data8), .out(out8));
    param_inst #(.WIDTH(16)) u16 (.clk(clk), .data(data16), .out(out16));
endmodule

// Test 15: 接口端口连接
module test_conn_interface;
    logic clk;
    logic [7:0] addr, data;
    
    simple_if if_inst (.clk(clk));
endmodule

interface simple_if (
    input logic clk
);
    logic [7:0] addr;
    logic [7:0] data;
endinterface

// Test 16: generate块中实例连接
module test_conn_gen_inst;
    logic clk;
    logic [7:0] out [0:3];
    
    genvar i;
    for (i = 0; i < 4; i++) begin : gen_conn
        gen_inst u_gi (.clk(clk), .out(out[i]));
    end
endmodule

module gen_inst (
    input  logic clk,
    output logic [7:0] out
);
    always_ff @(posedge clk)
        out <= 8'h00;
endmodule

// Test 17: 实例数组连接
module test_conn_inst_array;
    logic clk;
    logic [7:0] data_in [0:3];
    logic [7:0] data_out [0:3];
    
    arr_inst u_arr [0:3] (.*);
endmodule

module arr_inst (
    input  logic clk,
    input  logic [7:0] din,
    output logic [7:0] dout
);
    always_ff @(posedge clk)
        dout <= din;
endmodule

// Test 18: 跨时钟域连接
module test_conn_cdc;
    logic src_clk, dst_clk;
    logic [7:0] src_data, dst_data;
    
    cdc_reg u_cdc (
        .src_clk(src_clk),
        .dst_clk(dst_clk),
        .src_data(src_data),
        .dst_data(dst_data)
    );
endmodule

module cdc_reg (
    input  logic src_clk, dst_clk,
    input  logic [7:0] src_data,
    output logic [7:0] dst_data
);
    logic [7:0] sync_reg;
    
    always_ff @(posedge dst_clk)
        sync_reg <= src_data;
    
    always_ff @(posedge dst_clk)
        dst_data <= sync_reg;
endmodule
