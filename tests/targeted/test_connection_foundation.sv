// ============================================================================
// ConnectionAnalyzer 底层功能测试
// 测试模块连接分析的各种场景
// ============================================================================

// Test 1: 简单模块连接
module module_a (
    input  logic clk,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    always_ff @(posedge clk) begin
        data_out <= data_in + 1;
    end
endmodule

module top_simple_conn;
    logic clk;
    logic [7:0] data1, data2;
    
    module_a u_a (
        .clk(clk),
        .data_in(data1),
        .data_out(data2)
    );
endmodule


// Test 2: 多模块连接链
module unit_delay (
    input  logic clk,
    input  logic [7:0] din,
    output logic [7:0] dout
);
    always_ff @(posedge clk)
        dout <= din;
endmodule

module chain_conn;
    logic clk;
    logic [7:0] stage0, stage1, stage2, stage3;
    
    unit_delay u0 (.clk(clk), .din(stage0), .dout(stage1));
    unit_delay u1 (.clk(clk), .din(stage1), .dout(stage2));
    unit_delay u2 (.clk(clk), .din(stage2), .dout(stage3));
endmodule


// Test 3: 点对点连接
module point_to_point;
    logic [7:0] sig_a, sig_b, sig_c;
    
    assign sig_b = sig_a;
    assign sig_c = sig_b;
endmodule


// Test 4: 总线连接
module bus_conn;
    logic [31:0] bus_data;
    logic [7:0] byte0, byte1, byte2, byte3;
    logic [7:0] recombined;
    
    // 拆分
    assign byte0 = bus_data[7:0];
    assign byte1 = bus_data[15:8];
    assign byte2 = bus_data[23:16];
    assign byte3 = bus_data[31:24];
    
    // 重组
    assign recombined = {byte0, byte1, byte2, byte3};
endmodule


// Test 5: 广播连接
module broadcast_conn;
    logic enable;
    logic [7:0] source;
    logic [7:0] dest1, dest2, dest3, dest4;
    
    assign dest1 = enable ? source : 8'h00;
    assign dest2 = enable ? source : 8'h00;
    assign dest3 = enable ? source : 8'h00;
    assign dest4 = enable ? source : 8'h00;
endmodule


// Test 6: 多路复用连接
module mux_conn;
    logic [1:0] sel;
    logic [7:0] in0, in1, in2, in3;
    logic [7:0] out;
    
    assign out = (sel == 2'b00) ? in0 :
                (sel == 2'b01) ? in1 :
                (sel == 2'b10) ? in2 : in3;
endmodule


// Test 7: 层次化连接
module sub_module (
    input  logic clk,
    input  logic [7:0] din,
    output logic [7:0] dout
);
    logic [7:0] internal;
    always_ff @(posedge clk) begin
        internal <= din;
        dout <= internal + 1;
    end
endmodule

module hierarchical_conn;
    logic clk;
    logic [7:0] a_in, a_out, b_in, b_out;
    
    sub_module u_a (.clk(clk), .din(a_in), .dout(a_out));
    sub_module u_b (.clk(clk), .din(a_out), .dout(b_out));
endmodule


// Test 8: 未连接端口
module unconnected_ports (
    input  logic clk,
    input  logic [7:0] data_in,
    output logic [7:0] data_out,
    output logic valid,  // 未连接
    input  ready       // 未连接
);
    always_ff @(posedge clk) begin
        data_out <= data_in;
    end
    // valid和ready未连接
endmodule


// Test 9: 反向连接
module reverse_conn (
    input  logic clk,
    output logic [7:0] data_out,  // 反向: input端口
    input  logic [7:0] data_in      // 反向: output端口
);
    assign data_out = data_in;
endmodule


// Test 10: 参数化连接
module param_port #(
    parameter WIDTH = 8
) (
    input  logic clk,
    input  logic [WIDTH-1:0] din,
    output logic [WIDTH-1:0] dout
);
    always_ff @(posedge clk)
        dout <= din;
endmodule

module param_conn;
    logic clk;
    logic [7:0] data8;
    logic [15:0] data16;
    
    param_port #(.WIDTH(8)) u8 (.clk(clk), .din(data8), .dout(data8));
    param_port #(.WIDTH(16)) u16 (.clk(clk), .din(data16), .dout(data16));
endmodule
