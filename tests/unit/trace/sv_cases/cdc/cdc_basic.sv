// ============================================================================
// CDC 测试用例 - 跨时钟域
// ============================================================================

// 跨时钟域单 bit (无同步器 - 问题)
module cdc_single_bit_bad(
    input clk_a,
    input clk_b,
    input signal_in
);
    logic signal_out;
    
    always_ff @(posedge clk_b) begin
        signal_out <= signal_in;  // 问题: 无同步器
    end
endmodule

// 跨时钟域单 bit (有同步器 - OK)
module cdc_single_bit_good(
    input clk_a,
    input clk_b,
    input signal_in
);
    logic sync1, sync2, signal_out;
    
    always_ff @(posedge clk_b) begin
        sync1 <= signal_in;
        sync2 <= sync1;
        signal_out <= sync2;
    end
endmodule

// 多 bit 跨域 (无握手 - 问题)
module cdc_multi_bit_bad(
    input clk_a,
    input clk_b,
    input [7:0] data_in
);
    logic [7:0] data_out;
    
    always_ff @(posedge clk_b) begin
        data_out <= data_in;  // 问题: 多 bit 无握手
    end
endmodule

// 多 bit 跨域 (有 FIFO - OK)
module cdc_multi_bit_fifo(
    input clk_a,
    input clk_b,
    input [7:0] data_in,
    input wr_en,
    input rd_en,
    output [7:0] data_out,
    output full,
    output empty
);
    // 简单的异步 FIFO
    logic [7:0] mem [0:15];
    logic [3:0] wr_ptr, rd_ptr;
    
    always_ff @(posedge clk_a) begin
        if (wr_en && !full)
            mem[wr_ptr] <= data_in;
    end
    
    always_ff @(posedge clk_b) begin
        if (rd_en && !empty)
            data_out <= mem[rd_ptr];
    end
endmodule

// 异步复位跨域
module cdc_async_reset(
    input clk_a,
    input clk_b,
    input rst_n,
    input signal_in
);
    logic sync1, sync2, signal_out;
    
    always_ff @(posedge clk_b or negedge rst_n) begin
        if (!rst_n) begin
            sync1 <= 1'b0;
            sync2 <= 1'b0;
            signal_out <= 1'b0;
        end else begin
            sync1 <= signal_in;
            sync2 <= sync1;
            signal_out <= sync2;
        end
    end
endmodule
