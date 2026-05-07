// ============================================================================
// IOSpecExtractor 测试用例 - IO 规范
// ============================================================================

// 简单模块
module io_simple(
    input clk,
    input rst_n,
    input [7:0] data_in,
    input valid,
    output [7:0] data_out,
    output ready
);
    logic [7:0] temp;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            temp <= 8'h00;
        else if (valid)
            temp <= data_in;
    end
    
    assign data_out = temp;
    assign ready = valid;
endmodule

// 参数化模块
module io_param #(
    parameter WIDTH = 8,
    parameter DEPTH = 16
)(
    input clk,
    input rst_n,
    input [WIDTH-1:0] data_in,
    input valid,
    output [WIDTH-1:0] data_out,
    output [DEPTH-1:0] count,
    output full
);
    logic [WIDTH-1:0] mem [0:DEPTH-1];
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 0;
        end else if (valid && !full) begin
            mem[count] <= data_in;
            count <= count + 1;
        end
    end
    
    assign data_out = mem[count-1];
    assign full = (count >= DEPTH);
endmodule

// 完整接口模块
module io_full(
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
    output irq
);
    assign s_addr = m_addr;
    assign s_wdata = m_wdata;
    assign m_rdata = s_rdata;
    assign m_ready = s_ready;
    assign s_valid = m_valid;
    assign status = 4'h0;
    assign irq = 1'b0;
endmodule
