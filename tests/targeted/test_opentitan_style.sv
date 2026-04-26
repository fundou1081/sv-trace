// ============================================================================
// OpenTitan Style Corner Cases - 来自真实项目的Corner Case
// ============================================================================

// Test 1: 多级同步器链 (OpenTitan风格)
module multi_stage_sync (
    input  logic clk_i,
    input  logic rst_ni,
    input  logic [31:0] data_i,
    output logic [31:0] data_o
);
    // 3级同步器
    logic [31:0] sync_q0, sync_q1, sync_q2;
    
    always_ff @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            sync_q0 <= '0;
            sync_q1 <= '0;
            sync_q2 <= '0;
        end else begin
            sync_q0 <= data_i;
            sync_q1 <= sync_q0;
            sync_q2 <= sync_q1;
        end
    end
    
    assign data_o = sync_q2;
endmodule


// Test 2: Gray码计数器同步器
module gray_code_sync #(
    parameter int Width = 4
) (
    input  logic clk_src_i,
    input  logic clk_dst_i,
    input  logic rst_src_ni,
    input  logic rst_dst_ni,
    input  logic [Width-1:0] wptr_i,
    output logic [Width-1:0] wptr_sync_o
);
    logic [Width-1:0] wptr-gray;
    logic [1:0] meta_ff;
    
    // Binary to Gray
    assign wptr-gray = wptr_i ^ (wptr_i >> 1);
    
    // 同步到目标时钟域
    always_ff @(posedge clk_dst_i or negedge rst_dst_ni) begin
        if (!rst_dst_ni) begin
            meta_ff <= '0;
            wptr_sync_o <= '0;
        end else begin
            meta_ff <= {meta_ff[0], wptr-gray[Width-1]};
            wptr_sync_o <= {meta_ff[1], wptr-gray[Width-2:0]};
        end
    end
endmodule


// Test 3: 握手接口 (OpenTitan风格)
module handshake_receiver #(
    parameter int WIDTH = 32
) (
    input  logic clk_i,
    input  logic rst_ni,
    input  logic [WIDTH-1:0] data_i,
    input  logic valid_i,
    output logic ready_o,
    output logic [WIDTH-1:0] data_o,
    output logic valid_o
);
    // 2-phase handshake
    logic ready_q;
    logic trans_complete;
    
    assign ready_o = ready_q;
    assign trans_complete = valid_i & ready_q;
    
    always_ff @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            ready_q <= 1'b1;
            valid_o <= 1'b0;
            data_o <= '0;
        end else begin
            ready_q <= ready_q;
            valid_o <= 1'b0;
            
            if (trans_complete) begin
                data_o <= data_i;
                valid_o <= 1'b1;
                ready_q <= 1'b0;
            end else if (!valid_i) begin
                ready_q <= 1'b1;
            end
        end
    end
endmodule


// Test 4: 异步FIFO (OpenTitan风格)
module async_fifo #(
    parameter int DEPTH = 16,
    parameter int WIDTH = 32
) (
    input  logic clk_wr_i,
    input  logic clk_rd_i,
    input  logic rst_wr_ni,
    input  logic rst_rd_ni,
    input  logic [WIDTH-1:0] wdata_i,
    input  logic wvalid_i,
    output logic wready_o,
    input  logic rvalid_i,
    output logic [WIDTH-1:0] rdata_o,
    output logic rempty_o,
    output logic rfull_o
);
    localparam int ADDR_WIDTH = $clog2(DEPTH);
    
    // 写指针
    logic [ADDR_WIDTH:0] wptr_bin;
    logic [ADDR_WIDTH:0] wptr_gray, wptr_gray_sync;
    logic [1:0] wptr_meta;
    
    // 读指针
    logic [ADDR_WIDTH:0] rptr_bin;
    logic [ADDR_WIDTH:0] rptr_gray, rptr_gray_sync;
    logic [1:0] rptr_meta;
    
    // Memory
    logic [WIDTH-1:0] mem [0:DEPTH-1];
    
    // Write domain
    always_ff @(posedge clk_wr_i or negedge rst_wr_ni) begin
        if (!rst_wr_ni) begin
            wptr_bin <= '0;
        end else if (wvalid_i && !wfull_o) begin
            mem[wptr_bin[ADDR_WIDTH-1:0]] <= wdata_i;
            wptr_bin <= wptr_bin + 1;
        end
    end
    
    assign wptr_gray = wptr_bin ^ (wptr_bin >> 1);
    
    // Gray码同步
    always_ff @(posedge clk_rd_i or negedge rst_rd_ni) begin
        if (!rst_rd_ni) begin
            wptr_meta <= '0;
            wptr_gray_sync <= '0;
        end else begin
            wptr_meta <= {wptr_meta[0], wptr_gray[ADDR_WIDTH]};
            wptr_gray_sync <= {wptr_meta[1], wptr_gray[ADDR_WIDTH-1:0]};
        end
    end
    
    // Read domain
    always_ff @(posedge clk_rd_i or negedge rst_rd_ni) begin
        if (!rst_rd_ni) begin
            rptr_bin <= '0;
            rdata_o <= '0;
        end else if (rvalid_i && !rempty_o) begin
            rdata_o <= mem[rptr_bin[ADDR_WIDTH-1:0]];
            rptr_bin <= rptr_bin + 1;
        end
    end
    
    assign rptr_gray = rptr_bin ^ (rptr_bin >> 1);
    
    // Gray码同步回写时钟域
    always_ff @(posedge clk_wr_i or negedge rst_wr_ni) begin
        if (!rst_wr_ni) begin
            rptr_meta <= '0;
            rptr_gray_sync <= '0;
        end else begin
            rptr_meta <= {rptr_meta[0], rptr_gray[ADDR_WIDTH]};
            rptr_gray_sync <= {rptr_meta[1], rptr_gray[ADDR_WIDTH-1:0]};
        end
    end
    
    // 空满判断
    assign rempty_o = (wptr_gray_sync == rptr_gray);
    assign rfull_o = (wptr_gray[ADDR_WIDTH] != rptr_gray_sync[ADDR_WIDTH]) &&
                     (wptr_gray[ADDR_WIDTH-1:0] == rptr_gray_sync[ADDR_WIDTH-1:0]);
endmodule


// Test 5: 复位策略 (OpenTitan风格)
module reset_strategy #(
    parameter int NUM_DOMAINS = 2
) (
    input  logic clk_i,
    input  logic rst_ni,
    input  logic [NUM_DOMAINS-1:0] rst_reqs_i,
    output logic [NUM_DOMAINS-1:0] rst_acks_o,
    input  logic scan_mode_i
);
    // 断言rst_reqs_i保持稳定直到对应的rst_ack
    for (genvar i = 0; i < NUM_DOMAINS; i++) begin : gen_rst_chains
        logic [2:0] rst_sync_q;
        
        always_ff @(posedge clk_i or negedge rst_ni) begin
            if (!rst_ni) begin
                rst_sync_q <= '0;
            end else begin
                rst_sync_q <= {rst_sync_q[1:0], rst_reqs_i[i]};
            end
        end
        
        assign rst_acks_o[i] = rst_sync_q[2];
    end
endmodule


// Test 6: 多路选择器树 (OpenTitan风格)
module mux_tree #(
    parameter int N = 8,
    parameter int WIDTH = 32
) (
    input  logic [N-1:0][WIDTH-1:0] data_i,
    input  logic [$clog2(N)-1:0] sel_i,
    output logic [WIDTH-1:0] data_o
);
    // 二叉树结构
    localparam int DEPTH = $clog2(N);
    
    logic [WIDTH-1:0] level [0:DEPTH][0:N-1];
    
    // Level 0: 输入
    for (genvar i = 0; i < N; i++) begin : gen_level0
        assign level[0][i] = data_i[i];
    end
    
    // 中间层
    for (genvar d = 0; d < DEPTH; d++) begin : gen_levels
        for (genvar i = 0; i < N; i += 2) begin : gen_mux
            if (i + 1 < N) begin : gen_mux_valid
                assign level[d+1][i/2] = (sel_i[d] == 1'b0) ?
                                            level[d][i] : level[d][i+1];
            end else begin : gen_mux_passthrough
                assign level[d+1][i/2] = level[d][i];
            end
        end
    end
    
    assign data_o = level[DEPTH][0];
endmodule


// Test 7: 脉冲同步器
module pulse_sync #(
    parameter int NUM_STAGES = 3
) (
    input  logic clk_src_i,
    input  logic clk_dst_i,
    input  logic rst_src_ni,
    input  logic rst_dst_ni,
    input  logic src_pulse_i,
    output logic dst_pulse_o
);
    logic src_level, dst_level;
    logic [NUM_STAGES-1:0] sync_regs;
    
    // 边沿检测
    logic src_pulse_d;
    always_ff @(posedge clk_src_i or negedge rst_src_ni) begin
        if (!rst_src_ni) begin
            src_pulse_d <= 1'b0;
            src_level <= 1'b0;
        end else begin
            src_pulse_d <= src_pulse_i;
            src_level <= src_level ^ src_pulse_i;
        end
    end
    
    // 同步
    always_ff @(posedge clk_dst_i or negedge rst_dst_ni) begin
        if (!rst_dst_ni) begin
            sync_regs <= '0;
        end else begin
            sync_regs <= {sync_regs[NUM_STAGES-2:0], src_level};
        end
    end
    
    // 边沿检测产生输出脉冲
    assign dst_pulse_o = sync_regs[NUM_STAGES-1] ^ sync_regs[NUM_STAGES-2];
endmodule


// Test 8: 计数器跨时钟域
module counter_cdc #(
    parameter int WIDTH = 8
) (
    input  logic src_clk_i,
    input  logic dst_clk_i,
    input  logic src_rst_ni,
    input  logic dst_rst_ni,
    input  logic src_inc_i,
    input  logic dst_sample_i,
    output logic [WIDTH-1:0] dst_count_o
);
    logic [WIDTH-1:0] src_counter;
    logic src_inc_d;
    
    // 源时钟域计数
    always_ff @(posedge src_clk_i or negedge src_rst_ni) begin
        if (!src_rst_ni) begin
            src_counter <= '0;
            src_inc_d <= 1'b0;
        end else begin
            src_inc_d <= src_inc_i;
            if (src_inc_i && !src_inc_d) begin
                src_counter <= src_counter + 1;
            end
        end
    end
    
    // Gray码转换
    logic [WIDTH:0] src_gray;
    assign src_gray = src_counter ^ (src_counter >> 1);
    
    // 2级同步到目标时钟域
    logic [WIDTH:0] dst_gray_meta, dst_gray_sync;
    
    always_ff @(posedge dst_clk_i or negedge dst_rst_ni) begin
        if (!dst_rst_ni) begin
            dst_gray_meta <= '0;
            dst_gray_sync <= '0;
        end else begin
            dst_gray_meta <= src_gray;
            dst_gray_sync <= dst_gray_meta;
        end
    end
    
    // Gray到binary
    logic [WIDTH:0] dst_binary;
    for (genvar i = 0; i <= WIDTH; i++) begin : gen_gray2bin
        logic [i:0] gray_bits;
        assign gray_bits = dst_gray_sync[i:0];
        for (genvar j = 1; j < i; j++) begin : gen_xor
            assign gray_bits = gray_bits ^ dst_gray_sync[i-j:0];
        end
    end
    
    // 带采样信号的计数输出
    always_ff @(posedge dst_clk_i or negedge dst_rst_ni) begin
        if (!dst_rst_ni) begin
            dst_count_o <= '0;
        end else if (dst_sample_i) begin
            dst_count_o <= dst_binary[WIDTH-1:0];
        end
    end
endmodule
