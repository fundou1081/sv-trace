// ============================================================================
// IOSpecExtractor 测试用例 - 20个 IO 语法组合
// ============================================================================

// 1. 简单 input
module io_01_input_only;
    input clk;
endmodule

// 2. 简单 output
module io_02_output_only;
    output [7:0] data;
endmodule

// 3. input + output
module io_03_input_output;
    input clk;
    output [7:0] data;
endmodule

// 4. 带宽度
module io_04_with_width;
    input [31:0] data_in;
    output [31:0] data_out;
endmodule

// 5. 向量信号
module io_05_vector;
    input [7:0] vec [0:3];
    output [7:0] result;
endmodule

// 6. 异步复位
module io_06_async_reset;
    input clk, rst_n;
    input [7:0] data_in;
    output [7:0] data_out;
endmodule

// 7. 同步复位
module io_07_sync_reset;
    input clk, rst;
    input [7:0] data_in;
    output [7:0] data_out;
endmodule

// 8. inout (三态)
module io_08_inout;
    inout [7:0] data_bus;
endmodule

// 9. 混合方向
module io_09_mixed_dir;
    input clk, rst_n;
    input [7:0] data_in;
    output [7:0] data_out;
    inout [7:0] data_bus;
endmodule

// 10. 参数化模块
module io_10_param #(
    parameter WIDTH = 8
)(
    input clk,
    input [WIDTH-1:0] data_in,
    output [WIDTH-1:0] data_out
);
endmodule

// 11. 多参数
module io_11_multi_param #(
    parameter WIDTH = 8,
    parameter DEPTH = 16,
    parameter ADDR_W = 4
)(
    input clk,
    input [ADDR_W-1:0] addr,
    input [WIDTH-1:0] data_in,
    output [WIDTH-1:0] data_out
);
endmodule

// 12. 打包结构
module io_12_packed;
    input clk, rst_n;
    input [31:0] data_in;
    output [31:0] data_out;
    input [3:0] be;  // byte enable
endmodule

// 13. 握手信号
module io_13_handshake;
    input clk, rst_n;
    input [7:0] data_in;
    input valid,
    output ready,
    output [7:0] data_out;
endmodule

// 14. 完整总线接口
module io_14_bus_if;
    input clk, rst_n;
    input [31:0] addr;
    input [31:0] wdata;
    output [31:0] rdata;
    input we, valid;
    output ready;
endmodule

// 15. 时钟门控
module io_15_clk_gate;
    input clk, clk_en, rst_n;
    input [7:0] data_in;
    output [7:0] data_out;
endmodule

// 16. 多时钟
module io_16_multi_clk;
    input clk_a, clk_b, rst_n;
    input [7:0] data_in_a;
    input [7:0] data_in_b;
    output [7:0] data_out;
endmodule

// 17. 中断信号
module io_17_with_irq;
    input clk, rst_n;
    input [7:0] data_in;
    output irq;
    output [7:0] status;
endmodule

// 18. 调试接口
module io_18_debug;
    input clk, rst_n;
    input [7:0] dbg_data;
    input dbg_valid;
    output dbg_ready;
endmodule

// 19. 本地参数
module io_19_localparam;
    localparam ADDR_W = 8;
    localparam DATA_W = 32;
    input clk;
    input [ADDR_W-1:0] addr;
    input [DATA_W-1:0] data_in;
    output [DATA_W-1:0] data_out;
endmodule

// 20. 复杂接口组合
module io_20_complex;
    // Clock & Reset
    input clk,
    input rst_n,
    
    // Master Interface
    input [31:0] m_addr,
    input [31:0] m_wdata,
    output [31:0] m_rdata,
    input m_valid,
    output m_ready,
    
    // Slave Interface
    output [31:0] s_addr,
    output [31:0] s_wdata,
    input [31:0] s_rdata,
    output s_valid,
    input s_ready,
    
    // Status
    output [3:0] status,
    output irq,
    
    // Debug
    input [7:0] dbg_data,
    input dbg_valid,
    output dbg_ready
);
endmodule
