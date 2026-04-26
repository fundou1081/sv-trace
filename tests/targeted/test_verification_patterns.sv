// ============================================================================
// Verification Pattern Corner Cases - 验证相关的Corner Case
// ============================================================================

// Test 1: 无锁存器验证 - 完整的if-else
module complete_if_else;
    logic [7:0] a, b, result;
    logic valid;
    
    always_comb begin
        if (valid) begin
            result = a + b;
        end else begin
            result = 8'h00;
        end
    end
endmodule


// Test 2: 锁存器 (避免)
module latch_inference_bad;
    logic [7:0] a, b, result;
    logic valid;
    
    always_comb begin
        if (valid)
            result = a + b;
        // 没有else分支，会产生锁存器
    end
endmodule


// Test 3: Full case / Parallel case
module full_parallel_case;
    logic [1:0] sel;
    logic [7:0] a, b, c, d, result;
    
    // full_case: 所有情况都有覆盖
    always_comb begin
        case (sel)  // synthesis full_case
            2'b00: result = a;
            2'b01: result = b;
            2'b10: result = c;
            2'b11: result = d;
        endcase
    end
    
    // parallel_case: 没有并行选择
    always_comb begin
        result = a;  // 默认
        case (sel)  // synthesis parallel_case
            2'b00: result = a;
            2'b01: result = b;
            2'b10: result = c;
            2'b11: result = d;
        endcase
    end
endmodule


// Test 4: 状态机One-hot编码
module fsm_onehot_safe (
    input  logic clk,
    input  logic rst_n,
    input  logic start,
    output logic done
);
    typedef enum logic [3:0] {
        IDLE   = 4'b0001,
        READY  = 4'b0010,
        BUSY   = 4'b0100,
        DONE   = 4'b1000
    } state_t;
    
    state_t state, next_state;
    
    // 状态寄存器
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end
    
    // 下一状态逻辑
    always_comb begin
        next_state = state;
        case (1'b1)  // One-hot case
            state[0]: if (start) next_state = READY;  // IDLE
            state[1]: next_state = BUSY;  // READY
            state[2]: next_state = DONE;  // BUSY
            state[3]: next_state = IDLE;  // DONE
        endcase
    end
    
    assign done = state[3];
endmodule


// Test 5: 二段式状态机 vs 三段式状态机
module fsm_two_segment (
    input  logic clk,
    input  logic rst_n,
    input  logic req,
    output logic grant
);
    typedef enum logic [1:0] {IDLE, REQ, GRANT} state_t;
    state_t state, next;
    
    // 段1: 状态更新
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next;
    end
    
    // 段2: 下一状态和输出
    always_comb begin
        next = state;
        grant = 1'b0;
        case (state)
            IDLE: if (req) next = REQ;
            REQ: begin
                next = GRANT;
                grant = 1'b1;
            end
            GRANT: if (!req) next = IDLE;
        endcase
    end
endmodule


module fsm_three_segment (
    input  logic clk,
    input  logic rst_n,
    input  logic req,
    output logic grant
);
    typedef enum logic [1:0] {IDLE, REQ, GRANT} state_t;
    state_t state, next;
    logic grant_comb;
    
    // 段1: 状态更新
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next;
    end
    
    // 段2: 下一状态逻辑
    always_comb begin
        next = state;
        case (state)
            IDLE: if (req) next = REQ;
            REQ: next = GRANT;
            GRANT: if (!req) next = IDLE;
        endcase
    end
    
    // 段3: 输出逻辑
    always_comb begin
        grant_comb = 1'b0;
        case (state)
            REQ, GRANT: grant_comb = 1'b1;
        endcase
    end
    
    assign grant = grant_comb;
endmodule


// Test 6: 初始化模式
module initialization_patterns;
    logic clk;
    logic rst_n;
    logic [7:0] counter1, counter2, counter3, counter4;
    
    // 模式1: 异步复位
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            counter1 <= 8'h00;
        else
            counter1 <= counter1 + 1;
    end
    
    // 模式2: 同步复位
    always_ff @(posedge clk) begin
        if (!rst_n)
            counter2 <= 8'h00;
        else
            counter2 <= counter2 + 1;
    end
    
    // 模式3: 同步复位(else分支)
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            counter3 <= 8'h00;
        end else begin
            counter3 <= counter3 + 1;
        end
    end
    
    // 模式4: 无复位(上电随机)
    always_ff @(posedge clk)
        counter4 <= counter4 + 1;
endmodule


// Test 7: 无符号 vs 有符号运算
module signed_unsigned_ops;
    logic [7:0] a_unsigned;
    logic signed [7:0] b_signed;
    logic signed [15:0] result_mul;
    logic [7:0] result_div;
    logic result_lt, result_lt_signed;
    
    // 无符号乘法
    assign result_mul = a_unsigned * b_signed;  // 结果自动扩展
    
    // 有符号除法
    assign result_div = a_unsigned / b_signed[7:0];
    
    // 无符号比较
    assign result_lt = a_unsigned < b_signed;
    
    // 有符号比较
    assign result_lt_signed = a_unsigned < b_signed;
endmodule


// Test 8: Xprop (X乐观/悲观)
module xprop_handling;
    logic [7:0] a;
    logic [7:0] b;
    logic [7:0] result_add;
    logic [7:0] result_mux;
    logic sel;
    
    // 加法: X传播
    assign result_add = a + b;
    
    // MUX: if-else保证
    always_comb begin
        if (sel)
            result_mux = a;
        else
            result_mux = b;
    end
    
    // MUX: 三元可能产生X
    // assign result_mux = sel ? a : b;  // 可能产生X
endmodule


// Test 9: 层次化设计 - 跨模块端口
module sub_module (
    input  logic clk,
    input  logic rst_n,
    input  logic [31:0] data_in,
    output logic [31:0] data_out,
    input  logic valid_in,
    output logic valid_out
);
    logic [31:0] pipeline_reg;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pipeline_reg <= 32'h0;
            valid_out <= 1'b0;
        end else begin
            pipeline_reg <= data_in;
            valid_out <= valid_in;
        end
    end
    
    assign data_out = pipeline_reg;
endmodule

module top_hierarchy (
    input  logic clk,
    input  logic rst_n,
    input  logic [31:0] ext_data,
    output logic [31:0] result,
    input  logic ext_valid,
    output logic ext_ready
);
    logic [31:0] stage1_data, stage2_data;
    logic stage1_valid, stage2_valid;
    
    // 实例1
    sub_module u_stage1 (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(ext_data),
        .data_out(stage1_data),
        .valid_in(ext_valid),
        .valid_out(stage1_valid)
    );
    
    // 实例2
    sub_module u_stage2 (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(stage1_data),
        .data_out(stage2_data),
        .valid_in(stage1_valid),
        .valid_out(stage2_valid)
    );
    
    assign result = stage2_data;
    assign ext_ready = stage2_valid;
endmodule


// Test 10: 参数化设计
module generic_mux #(
    parameter int WIDTH = 8,
    parameter int N_INPUTS = 4
) (
    input  logic [N_INPUTS-1:0][WIDTH-1:0] data_in,
    input  logic [$clog2(N_INPUTS)-1:0] sel,
    output logic [WIDTH-1:0] data_out
);
    // 参数化MUX实现
    assign data_out = data_in[sel];
endmodule

module param_usage;
    // 实例化不同参数
    generic_mux #(.WIDTH(8), .N_INPUTS(4)) u_mux4x8 (...);
    generic_mux #(.WIDTH(16), .N_INPUTS(8)) u_mux8x16 (...);
endmodule
