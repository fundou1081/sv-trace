// ============================================================================
// CDC Corner Cases - 跨时钟域边界测试
// ============================================================================

// Test 1: 不安全的1级同步器(应该被检测)
module cdc_unsafe_1ff (
    input  logic clk_b,
    input  logic rst_n,
    input  logic data_in,
    output logic data_out
);
    // 1级同步器 - 高风险!
    always_ff @(posedge clk_b or negedge rst_n) begin
        if (!rst_n)
            data_out <= 1'b0;
        else
            data_out <= data_in;  // 直接跨时钟域，无同步!
    end
endmodule


// Test 2: 握手协议CDC
module cdc_handshake (
    input  logic clk_a,
    input  logic clk_b,
    input  logic rst_n,
    input  logic req_a,
    output logic ack_a,
    output logic data_out
);
    // Request同步到clk_b
    logic req_b_sync;
    logic [1:0] req_b_sync2;
    always_ff @(posedge clk_b or negedge rst_n) begin
        if (!rst_n) begin
            req_b_sync2 <= 2'b0;
        end else begin
            req_b_sync2 <= {req_b_sync2[0], req_a};
        end
    end
    assign req_b_sync = req_b_sync2[1];
    
    // Ack同步回clk_a
    logic ack_a_sync;
    logic [1:0] ack_a_sync2;
    always_ff @(posedge clk_a or negedge rst_n) begin
        if (!rst_n) begin
            ack_a_sync2 <= 2'b0;
        end else begin
            ack_a_sync2 <= {ack_a_sync2[0], req_b_sync};
        end
    end
    assign ack_a = ack_a_sync2[1];
    
    // 数据在req_b_sync上升沿采样
    always_ff @(posedge clk_b or negedge rst_n) begin
        if (!rst_n)
            data_out <= 1'b0;
        else if (req_b_sync && !ack_a_sync2[0])
            data_out <= req_a;
    end
endmodule


// Test 3: Mux同步器(多bit CDC)
module cdc_mux_sync (
    input  logic clk_b,
    input  logic rst_n,
    input  logic sel,
    input  logic [7:0] data0,
    input  logic [7:0] data1,
    output logic [7:0] data_out
);
    // Mux同步器: 在sel稳定后才输出数据
    logic [7:0] data0_sync, data1_sync;
    logic [1:0] sel_sync;
    logic sel_stable;
    
    always_ff @(posedge clk_b or negedge rst_n) begin
        if (!rst_n) begin
            data0_sync <= 8'b0;
            data1_sync <= 8'b0;
            sel_sync <= 2'b0;
        end else begin
            data0_sync <= data0;
            data1_sync <= data1;
            sel_sync <= {sel_sync[0], sel};
        end
    end
    
    assign sel_stable = (sel_sync[0] == sel_sync[1]);
    assign data_out = sel_sync[1] ? data1_sync : data0_sync;
endmodule


// Test 4: 复位信号跨时钟域
module cdc_reset_cross (
    input  logic clk_a,
    input  logic clk_b,
    input  logic rst_n,
    output logic rst_a_sync,
    output logic rst_b_sync
);
    // 主复位同步到clk_a
    logic [2:0] rst_a_sync_reg;
    always_ff @(posedge clk_a or negedge rst_n) begin
        if (!rst_n)
            rst_a_sync_reg <= 3'b111;
        else
            rst_a_sync_reg <= {rst_a_sync_reg[1:0], 1'b1};
    end
    assign rst_a_sync = rst_a_sync_reg[2];
    
    // 主复位同步到clk_b
    logic [2:0] rst_b_sync_reg;
    always_ff @(posedge clk_b or negedge rst_n) begin
        if (!rst_n)
            rst_b_sync_reg <= 3'b111;
        else
            rst_b_sync_reg <= {rst_b_sync_reg[1:0], 1'b1};
    end
    assign rst_b_sync = rst_b_sync_reg[2];
endmodule


// Test 5: 门控时钟下的CDC
module cdc_gated_clock (
    input  logic clk,
    input  logic clk_en,
    input  logic clk_b,
    input  logic rst_n,
    input  logic data_in,
    output logic data_out
);
    // 门控时钟
    logic gated_clk;
    assign gated_clk = clk && clk_en;
    
    // 数据在门控时钟域
    logic data_gated;
    always_ff @(posedge gated_clk or negedge rst_n) begin
        if (!rst_n)
            data_gated <= 1'b0;
        else
            data_gated <= data_in;
    end
    
    // 跨到clk_b
    logic [1:0] sync;
    always_ff @(posedge clk_b or negedge rst_n) begin
        if (!rst_n)
            sync <= 2'b0;
        else
            sync <= {sync[0], data_gated};
    end
    assign data_out = sync[1];
endmodule


// Test 6: 异步复位释放与时钟沿同时(亚稳态风险)
module cdc_reset_release_race (
    input  logic clk,
    input  logic async_rst_n,  // 异步复位，低有效
    output logic rst_sync
);
    // 异步复位，同步释放 - 但释放时机与时钟沿可能冲突
    logic [2:0] rst_sync_reg;
    
    always_ff @(posedge clk or negedge async_rst_n) begin
        if (!async_rst_n)
            rst_sync_reg <= 3'b000;
        else
            rst_sync_reg <= {rst_sync_reg[1:0], 1'b1};
    end
    
    assign rst_sync = rst_sync_reg[2];
endmodule


// Test 7: 快时钟到慢时钟CDC
module cdc_fast_to_slow (
    input  logic fast_clk,
    input  logic slow_clk,
    input  logic rst_n,
    input  logic [7:0] data_fast,
    input  logic data_valid,
    output logic [7:0] data_out
);
    // 快时钟域: 数据和valid
    logic [7:0] data_hold;
    logic valid_hold;
    
    always_ff @(posedge fast_clk or negedge rst_n) begin
        if (!rst_n) begin
            data_hold <= 8'b0;
            valid_hold <= 1'b0;
        end else if (data_valid) begin
            data_hold <= data_fast;
            valid_hold <= 1'b1;
        end else if (valid_hold && ack_received) begin
            valid_hold <= 1'b0;  // 清除hold
        end
    end
    
    // Handshake
    logic req, ack, ack_received;
    logic [1:0] ack_sync;
    
    always_ff @(posedge fast_clk or negedge rst_n) begin
        if (!rst_n)
            ack_sync <= 2'b0;
        else
            ack_sync <= {ack_sync[0], ack};
    end
    assign ack_received = ack_sync[1];
    
    assign req = valid_hold;
    
    // 慢时钟域
    logic [1:0] req_sync;
    logic slow_req;
    
    always_ff @(posedge slow_clk or negedge rst_n) begin
        if (!rst_n) begin
            req_sync <= 2'b0;
            data_out <= 8'b0;
        end else begin
            req_sync <= {req_sync[0], req};
            slow_req <= req_sync[1];
            
            if (slow_req && !ack)
                data_out <= data_hold;
        end
    end
    
    assign ack = slow_req;  // 简单ack
endmodule


// Test 8: 多bit异步FIFO (Gray码指针)
module cdc_async_fifo_gray (
    input  logic wr_clk,
    input  logic rd_clk,
    input  logic rst_n,
    input  logic [7:0] wdata,
    input  logic wr_en,
    output logic [7:0] rdata,
    input  logic rd_en,
    output logic full,
    output logic empty
);
    parameter ADDR_WIDTH = 4;
    parameter DEPTH = 16;
    
    // Write domain
    logic [ADDR_WIDTH:0] wr_ptr_bin;
    logic [ADDR_WIDTH:0] wr_ptr_gray, wr_ptr_gray_sync;
    logic [1:0] wr_ptr_gray_meta;
    
    always_ff @(posedge wr_clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr_bin <= 0;
        end else if (wr_en && !full) begin
            wr_ptr_bin <= wr_ptr_bin + 1;
        end
    end
    
    // Binary to Gray
    assign wr_ptr_gray = wr_ptr_bin ^ (wr_ptr_bin >> 1);
    
    // Gray码同步到读时钟域
    always_ff @(posedge rd_clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr_gray_meta <= 0;
            wr_ptr_gray_sync <= 0;
        end else begin
            wr_ptr_gray_meta <= wr_ptr_gray;
            wr_ptr_gray_sync <= wr_ptr_gray_meta;
        end
    end
    
    // Read domain
    logic [ADDR_WIDTH:0] rd_ptr_bin;
    logic [ADDR_WIDTH:0] rd_ptr_gray, rd_ptr_gray_sync;
    logic [1:0] rd_ptr_gray_meta;
    
    always_ff @(posedge rd_clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_ptr_bin <= 0;
        end else if (rd_en && !empty) begin
            rd_ptr_bin <= rd_ptr_bin + 1;
        end
    end
    
    assign rd_ptr_gray = rd_ptr_bin ^ (rd_ptr_bin >> 1);
    
    // Gray码同步到写时钟域
    always_ff @(posedge wr_clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_ptr_gray_meta <= 0;
            rd_ptr_gray_sync <= 0;
        end else begin
            rd_ptr_gray_meta <= rd_ptr_gray;
            rd_ptr_gray_sync <= rd_ptr_gray_meta;
        end
    end
    
    // Full/Empty判断
    assign full = (wr_ptr_gray[ADDR_WIDTH] != rd_ptr_gray_sync[ADDR_WIDTH]) &&
                   (wr_ptr_gray[ADDR_WIDTH-1:0] == rd_ptr_gray_sync[ADDR_WIDTH-1:0]);
    assign empty = (wr_ptr_gray_sync == rd_ptr_gray);
    
    // Memory
    logic [7:0] mem [0:DEPTH-1];
    
    always_ff @(posedge wr_clk) begin
        if (wr_en && !full)
            mem[wr_ptr_bin[ADDR_WIDTH-1:0]] <= wdata;
    end
    
    always_ff @(posedge rd_clk) begin
        if (rd_en && !empty)
            rdata <= mem[rd_ptr_bin[ADDR_WIDTH-1:0]];
    end
endmodule
