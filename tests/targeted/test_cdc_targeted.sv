// ============================================================================
// CDC Targeted Test Cases - 跨时钟域专项测试
// ============================================================================

// Test 1: 简单同步器 (2级寄存器)
module cdc_sync_2ff (
    input  logic clk_a,
    input  logic clk_b,
    input  logic rst_n,
    input  logic data_in,
    output logic data_out
);
    logic [1:0] sync_regs;
    
    // 2级同步器
    always_ff @(posedge clk_b or negedge rst_n) begin
        if (!rst_n)
            sync_regs <= 2'b0;
        else
            sync_regs <= {sync_regs[0], data_in};
    end
    
    assign data_out = sync_regs[1];
endmodule


// Test 2: 多时钟域设计
module cdc_multi_clock (
    input  logic fast_clk,
    input  logic slow_clk,
    input  logic rst_n,
    input  logic [7:0] data_fast,
    input  logic data_valid,
    output logic [7:0] data_out,
    output logic data_ready
);
    // 快速时钟域
    logic [7:0] data_buffer;
    logic buffer_full;
    
    always_ff @(posedge fast_clk or negedge rst_n) begin
        if (!rst_n) begin
            data_buffer <= 0;
            buffer_full <= 0;
        end else begin
            if (data_valid && !buffer_full) begin
                data_buffer <= data_fast;
                buffer_full <= 1;
            end
        end
    end
    
    // 慢速时钟域 - 跨时钟域采样
    logic [1:0] sync_valid;
    logic [7:0] sync_data;
    
    always_ff @(posedge slow_clk or negedge rst_n) begin
        if (!rst_n) begin
            sync_valid <= 0;
            data_out <= 0;
            data_ready <= 0;
        end else begin
            sync_valid <= {sync_valid[0], buffer_full};
            if (sync_valid[1] && !data_ready) begin
                data_out <= data_buffer;
                data_ready <= 1;
            end
        end
    end
endmodule


// Test 3: Gray码计数器 (CDC安全)
module cdc_gray_counter (
    input  logic clk,
    input  logic rst_n,
    input  logic enable,
    output logic [3:0] gray_out
);
    logic [3:0] binCounter;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            binCounter <= 0;
        end else if (enable) begin
            binCounter <= binCounter + 1;
        end
    end
    
    // Binary to Gray
    assign gray_out = binCounter ^ (binCounter >> 1);
endmodule


// Test 4: 多bit CDC (异步FIFO风格)
module cdc_async_fifo (
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
    // 写时钟域
    logic [7:0] mem [0:15];
    logic [3:0] wr_ptr;
    logic [3:0] wr_ptr_gray;
    
    always_ff @(posedge wr_clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= 0;
            full <= 0;
        end else if (wr_en && !full) begin
            mem[wr_ptr[3:0]] <= wdata;
            wr_ptr <= wr_ptr + 1;
        end
    end
    
    assign wr_ptr_gray = wr_ptr ^ (wr_ptr >> 1);
    
    // 读时钟域
    logic [3:0] rd_ptr;
    logic [3:0] rd_ptr_gray;
    logic [1:0] sync_ptr;
    
    always_ff @(posedge rd_clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_ptr <= 0;
            empty <= 1;
        end else begin
            sync_ptr <= {sync_ptr[0], wr_ptr_gray[1]};
            if (rd_en && !empty) begin
                rdata <= mem[rd_ptr[3:0]];
                rd_ptr <= rd_ptr + 1;
            end
        end
    end
    
    assign rd_ptr_gray = rd_ptr ^ (rd_ptr >> 1);
endmodule


// Test 5: 无保护的 CDC (风险案例)
module cdc_unprotected (
    input  logic clk_a,
    input  logic clk_b,
    input  logic rst_n,
    input  logic signal_a,
    output logic signal_b
);
    // 直接跨时钟域传递 - 有风险
    always_ff @(posedge clk_b) begin
        signal_b <= signal_a;
    end
endmodule
