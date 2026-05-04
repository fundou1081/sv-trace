// =============================================================================
// comprehensive_driver_load_test.sv - Driver/Load 追踪综合测试基准
//
// 作者: 芯片专家
// 日期: 2026-05-04
// 目的: 覆盖各种 driver/load 代码写法，用于验证 sv-trace 工具
//
// 测试覆盖:
// 1. 基本 always_ff, always_comb, always_latch
// 2. assign 连续赋值
// 3. 阻塞 vs 非阻塞赋值
// 4. 位选择 [7:0]、位拼接 {a, b}
// 5. 条件表达式 a ? b : c
// 6. generate 语句
// 7. for/foreach 循环
// 8. if/else 嵌套
// 9. case/casez/casex
// 10. 函数/任务
// 11. 状态机
// 12. 跨模块连接
// 13. 接口信号
// 14. 复位策略
// 15. 时钟门控
// 16. 流水线寄存器
// 17. 罕见写法: force/release, alias, program block
// =============================================================================

// =============================================================================
// 1. 基本 always_ff - 寄存器
// =============================================================================
module basic_registers (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    // 最基本的时序逻辑
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data_out <= 8'h00;
        else
            data_out <= data_in;
    end
endmodule


// =============================================================================
// 2. always_comb - 组合逻辑
// =============================================================================
module basic_combinational (
    input  logic [7:0] a,
    input  logic [7:0] b,
    input  logic       sel,
    output logic [7:0] result
);
    // 基本组合逻辑 - 多路选择器
    always_comb begin
        if (sel)
            result = a;
        else
            result = b;
    end
    
    // 也常用三元表达式
    logic [7:0] result_alias;
    assign result_alias = sel ? a : b;
endmodule


// =============================================================================
// 3. always_latch - 锁存器 (不推荐但需支持)
// =============================================================================
module basic_latch (
    input  logic enable,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    // 锁存器 - 隐式
    always_latch begin
        if (enable)
            data_out = data_in;
    end
endmodule


// =============================================================================
// 4. assign 连续赋值 - 线网驱动
// =============================================================================
module continuous_assignment (
    input  logic [3:0] a,
    input  logic [3:0] b,
    output logic [7:0] sum,
    output logic       carry,
    output logic [7:0] product
);
    // 基本连续赋值
    assign sum = a + b;
    
    // 多驱动源联合
    assign carry = (a[3] & b[3]) | (a[3] & sum[7]) | (b[3] & sum[7]);
    
    // 乘积
    assign product = a * b;
endmodule


// =============================================================================
// 5. 位选择和位拼接
// =============================================================================
module bit_operations (
    input  logic [15:0] data_in,
    output logic [7:0]  high_byte,
    output logic [7:0]  low_byte,
    output logic [15:0] byte_swap,
    output logic [31:0] concat_result
);
    // 位选择
    assign high_byte = data_in[15:8];
    assign low_byte = data_in[7:0];
    
    // 字节交换
    assign byte_swap = {low_byte, high_byte};
    
    // 多层拼接
    assign concat_result = {8'hFF, data_in, 8'h00};
    
    // 条件拼接
    logic [7:0] mid;
    assign mid = data_in[15:8] ^ data_in[7:0];
endmodule


// =============================================================================
// 6. 条件表达式
// =============================================================================
module conditional_expressions (
    input  logic [7:0]  a,
    input  logic [7:0]  b,
    input  logic        cond,
    output logic [7:0]  result1,
    output logic [7:0]  result2
);
    // 三元表达式
    assign result1 = cond ? a : b;
    
    // 嵌套三元
    assign result2 = cond ? (a > b ? a : b) : 8'h00;
    
    // 拼接中的条件表达式
    logic [15:0] mixed;
    assign mixed = {cond ? a : b, cond ? b : a};
endmodule


// =============================================================================
// 7. generate 语句 - 复制逻辑
// =============================================================================
module generate_replication (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] data_in,
    output logic [63:0] data_out
);
    // 8 个 8-bit 寄存器的流水线
    logic [63:0] pipeline_q;
    
    // generate for - 复制寄存器链
    generate
        for (genvar i = 0; i < 8; i++) begin : pipeline_regs
            if (i == 0) begin : first_reg
                always_ff @(posedge clk or negedge rst_n) begin
                    if (!rst_n)
                        pipeline_q[7:0] <= 8'h00;
                    else
                        pipeline_q[7:0] <= data_in;
                end
            end else begin : other_regs
                always_ff @(posedge clk or negedge rst_n) begin
                    if (!rst_n)
                        pipeline_q[i*8 +: 8] <= 8'h00;
                    else
                        pipeline_q[i*8 +: 8] <= pipeline_q[(i-1)*8 +: 8];
                end
            end
        end
    endgenerate
    
    assign data_out = pipeline_q;
endmodule


// =============================================================================
// 8. for 循环 - 组合逻辑展开
// =============================================================================
module for_loop_combinational (
    input  logic [31:0] vector_in [7:0],
    input  logic [2:0]  sel,
    output logic [31:0] vector_out,
    output logic [31:0] parity
);
    // 32-bit 输入向量中选择
    always_comb begin
        vector_out = 32'h0;
        for (int i = 0; i < 8; i++) begin
            if (i == sel)
                vector_out = vector_in[i];
        end
    end
    
    // 奇偶校验
    always_comb begin
        parity = 32'h0;
        for (int i = 0; i < 32; i++) begin
            parity[0] = parity[0] ^ vector_in[sel][i];
        end
    end
endmodule


// =============================================================================
// 9. if/else 嵌套 - 优先级编码器
// =============================================================================
module priority_encoder (
    input  logic [7:0] req,
    output logic [2:0] grant,
    output logic        valid
);
    // 嵌套 if - 优先级编码
    always_comb begin
        valid = 1'b0;
        grant = 3'h0;
        
        if (req[7]) begin
            valid = 1'b1;
            grant = 3'd7;
        end else if (req[6]) begin
            valid = 1'b1;
            grant = 3'd6;
        end else if (req[5]) begin
            valid = 1'b1;
            grant = 3'd5;
        end else if (req[4]) begin
            valid = 1'b1;
            grant = 3'd4;
        end else if (req[3]) begin
            valid = 1'b1;
            grant = 3'd3;
        end else if (req[2]) begin
            valid = 1'b1;
            grant = 3'd2;
        end else if (req[1]) begin
            valid = 1'b1;
            grant = 3'd1;
        end else if (req[0]) begin
            valid = 1'b1;
            grant = 3'd0;
        end
    end
endmodule


// =============================================================================
// 10. case 语句 - 指令解码
// =============================================================================
module instruction_decoder (
    input  logic [31:0] instruction,
    output logic        is_load,
    output logic        is_store,
    output logic        is_branch,
    output logic        is_arith
);
    // case 精确解码
    always_comb begin
        is_load = 1'b0;
        is_store = 1'b0;
        is_branch = 1'b0;
        is_arith = 1'b0;
        
        casez (instruction[6:0])  // 只解码 opcode
            7'b0000011: is_load = 1'b1;    // load
            7'b0100011: is_store = 1'b1;   // store
            7'b1100011: is_branch = 1'b1;  // branch
            7'b0110011: is_arith = 1'b1;   // arithmetic
            default: ;  // no operation
        endcase
    end
endmodule


// =============================================================================
// 11. 函数 - 组合逻辑函数
// =============================================================================
module function_usage (
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] sum,
    output logic       overflow
);
    // 函数定义
    function logic [7:0] add_with_carry;
        input logic [7:0] x;
        input logic [7:0] y;
        logic carry;
        begin
            carry = (x[7] & y[7]) | (x[7] & add_with_carry[7]) | (y[7] & add_with_carry[7]);
            add_with_carry = x + y;
            overflow = carry;
        end
    endfunction
    
    assign {overflow, sum} = add_with_carry(a, b);
endmodule


// =============================================================================
// 12. 任务 - 时序相关操作
// =============================================================================
module task_usage (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    // 任务定义
    task delayed_write;
        input logic [7:0] data;
        input int delay_cycles;
        int dly;
        begin
            for (dly = 0; dly < delay_cycles; dly++) begin
                @(posedge clk);
            end
            data_out <= data;
        end
    endtask
    
    // 调用任务
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data_out <= 8'h00;
        else if (data_in[7])  // MSB set triggers delayed write
            delayed_write(data_in, 2);
    end
endmodule


// =============================================================================
// 13. 状态机 - Moore 和 Mealy
// =============================================================================
module state_machine (
    input  logic clk,
    input  logic rst_n,
    input  logic start,
    input  logic done,
    output logic [1:0] state_out,
    output logic       busy
);
    // 状态定义
    typedef enum logic [1:0] {
        IDLE  = 2'b00,
        RUN   = 2'b01,
        WAIT  = 2'b10,
        DONE  = 2'b11
    } state_t;
    
    state_t state_q, state_d;
    
    // Moore 状态机 - 输出只依赖状态
    always_comb begin
        case (state_q)
            IDLE: begin
                busy = 1'b0;
                state_d = start ? RUN : IDLE;
            end
            RUN: begin
                busy = 1'b1;
                state_d = WAIT;
            end
            WAIT: begin
                busy = 1'b1;
                state_d = done ? DONE : WAIT;
            end
            DONE: begin
                busy = 1'b0;
                state_d = IDLE;
            end
        endcase
    end
    
    // 状态寄存器
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state_q <= IDLE;
        else
            state_q <= state_d;
    end
    
    assign state_out = state_q;
endmodule


// =============================================================================
// 14. 跨模块连接
// =============================================================================
module top_module (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] ext_data,
    output logic [7:0] result
);
    // 子模块实例
    logic [7:0] stage1_out, stage2_out;
    
    basic_registers stage1 (
        .clk      (clk),
        .rst_n    (rst_n),
        .data_in  (ext_data),
        .data_out (stage1_out)
    );
    
    basic_combinational stage2 (
        .a      (stage1_out),
        .b      (8'h55),
        .sel    (stage1_out[7]),
        .result (stage2_out)
    );
    
    basic_registers stage3 (
        .clk      (clk),
        .rst_n    (rst_n),
        .data_in  (stage2_out),
        .data_out (result)
    );
endmodule


// =============================================================================
// 15. 复位策略
// =============================================================================
module reset_strategies (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] async_data,
    output logic [7:0] sync_out,
    output logic [7:0] async_out
);
    // 同步复位 - 最常见
    always_ff @(posedge clk) begin
        if (!rst_n)
            sync_out <= 8'h00;
        else
            sync_out <= async_data;
    end
    
    // 异步复位
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            async_out <= 8'h00;
        else
            async_out <= async_data;
    end
    
    // 多级复位条件
    logic [7:0] multi_rst_out;
    logic init_done, warm_rst;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            multi_rst_out <= 8'h00;
        else if (!init_done)
            multi_rst_out <= 8'hAA;  // 初始化值
        else if (warm_rst)
            multi_rst_out <= 8'h55;  // 热复位值
        else
            multi_rst_out <= async_data;
    end
endmodule


// =============================================================================
// 16. 时钟门控
// =============================================================================
module clock_gating (
    input  logic clk,
    input  logic rst_n,
    input  logic gate_en,
    input  logic [7:0] data_in,
    output logic [7:0] gated_out,
    output logic [7:0] ungated_out
);
    // 门控时钟寄存器
    logic gated_clk;
    logic enable_latch;
    
    // 锁存器形式的时钟门控 (不推荐但常见)
    always_latch begin
        if (!clk)
            enable_latch = gate_en;
    end
    assign gated_clk = clk & enable_latch;
    
    // 使用门控时钟
    always_ff @(posedge gated_clk or negedge rst_n) begin
        if (!rst_n)
            gated_out <= 8'h00;
        else
            gated_out <= data_in;
    end
    
    // 普通寄存器对比
    always_ff @(posedge clk) begin
        if (!rst_n)
            ungated_out <= 8'h00;
        else
            ungated_out <= data_in;
    end
endmodule


// =============================================================================
// 17. 流水线寄存器
// =============================================================================
module pipeline_registers (
    input  logic clk,
    input  logic rst_n,
    input  logic [31:0] data_in,
    input  logic        valid_in,
    output logic [31:0] data_out,
    output logic         valid_out,
    input  logic        stall
);
    // 3 级流水线
    logic [31:0] pipe1_q, pipe2_q, pipe3_q;
    logic         valid1_q, valid2_q, valid3_q;
    
    // Stage 1
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pipe1_q <= 32'h0;
            valid1_q <= 1'b0;
        end else if (!stall) begin
            pipe1_q <= data_in;
            valid1_q <= valid_in;
        end
    end
    
    // Stage 2
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pipe2_q <= 32'h0;
            valid2_q <= 1'b0;
        end else if (!stall) begin
            pipe2_q <= pipe1_q;
            valid2_q <= valid1_q;
        end
    end
    
    // Stage 3
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pipe3_q <= 32'h0;
            valid3_q <= 1'b0;
        end else if (!stall) begin
            pipe3_q <= pipe2_q;
            valid3_q <= valid2_q;
        end
    end
    
    assign data_out = pipe3_q;
    assign valid_out = valid3_q;
endmodule


// =============================================================================
// 18. 罕见写法 - force/release
// =============================================================================
module force_release_test (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    logic [7:0] internal_sig;
    
    // 正常驱动
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            internal_sig <= 8'h00;
        else
            internal_sig <= data_in;
    end
    
    // force 通常用于调试和测试
    // assign data_out = internal_sig;  // 正常连接
    
    // 测试时可以用 force 覆盖信号
    // initial begin
    //     #10 force internal_sig = 8'hFF;
    //     #50 release internal_sig;
    // end
    
    assign data_out = internal_sig;
endmodule


// =============================================================================
// 19. 别名 (alias)
// =============================================================================
module alias_test (
    input  logic [7:0] byte_val,
    output logic        bit7_alias,
    output logic        parity_bit,
    output logic        sign_bit
);
    // alias - 同一信号的多个名字
    // SystemVerilog 允许以下写法
    logic [7:0] swizzled;
    
    assign swizzled = {byte_val[0], byte_val[1], byte_val[2], byte_val[3],
                       byte_val[4], byte_val[5], byte_val[6], byte_val[7]};
    
    // 这些实际上是组合逻辑赋值
    assign bit7_alias = byte_val[7];    // 最高位
    assign parity_bit = ^byte_val;       // 奇偶校验位
    assign sign_bit = byte_val[7];       // 符号位 (对有符号数)
endmodule


// =============================================================================
// 20. program block
// =============================================================================
module program_block_example (
    input  logic clk,
    input  logic rst_n
);
    logic [7:0] test_data;
    logic       test_valid;
    
    // program block 用于验证环境，与时钟进行正确同步
    program test_monitor (
        input clk,
        input rst_n
    );
        initial begin
            @(posedge clk or negedge rst_n);
            if (!rst_n) begin
                test_valid = 1'b0;
            end else begin
                test_valid = 1'b1;
            end
        end
    endprogram
    
    // 实例化 program
    test_monitor mon (clk, rst_n);
endmodule


// =============================================================================
// 21. 跨时钟域 - 异步 FIFO 指针
// =============================================================================
module cdc_pointers (
    input  logic src_clk,
    input  logic src_rst_n,
    input  logic [4:0] src_wptr,
    input  logic [4:0] src_rptr,
    
    input  logic dst_clk,
    input  logic dst_rst_n,
    output logic [4:0] dst_wptr,
    output logic [4:0] dst_rptr_sync
);
    // 源时钟域
    logic [4:0] wptr_gray;
    assign wptr_gray = src_wptr ^ (src_wptr >> 1);
    
    // 目标时钟域 - 两级同步器
    logic [4:0] wptr_sync_q1, wptr_sync_q2;
    
    always_ff @(posedge dst_clk or negedge dst_rst_n) begin
        if (!dst_rst_n) begin
            wptr_sync_q1 <= 5'h0;
            wptr_sync_q2 <= 5'h0;
        end else begin
            wptr_sync_q1 <= wptr_gray;
            wptr_sync_q2 <= wptr_sync_q1;
        end
    end
    
    assign dst_wptr = wptr_sync_q2;
    assign dst_rptr_sync = src_rptr;  // 简化的跨时钟域
endmodule


// =============================================================================
// 22. 复杂状态机的完整示例
// =============================================================================
module complex_fsm (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] cmd,
    input  logic       cmd_valid,
    output logic [15:0] result,
    output logic        done
);
    typedef enum logic [3:0] {
        IDLE      = 4'h0,
        DECODE    = 4'h1,
        LOAD_A    = 4'h2,
        LOAD_B    = 4'h3,
        EXECUTE   = 4'h4,
        STORE     = 4'h5,
        VERIFY    = 4'h6,
        ERROR     = 4'h7,
        RECOVER   = 4'h8,
        DONE      = 4'h9
    } state_t;
    
    state_t state_q, state_d;
    logic [7:0] acc_a, acc_b;
    logic [15:0] accumulator;
    
    // 状态转换逻辑 - Mealy 型
    always_comb begin
        state_d = state_q;
        done = 1'b0;
        
        case (state_q)
            IDLE: begin
                if (cmd_valid)
                    state_d = DECODE;
            end
            
            DECODE: begin
                case (cmd[1:0])
                    2'b00: state_d = LOAD_A;
                    2'b01: state_d = LOAD_B;
                    2'b10: state_d = EXECUTE;
                    2'b11: state_d = ERROR;
                endcase
            end
            
            LOAD_A: begin
                state_d = VERIFY;
            end
            
            LOAD_B: begin
                state_d = VERIFY;
            end
            
            EXECUTE: begin
                state_d = STORE;
            end
            
            VERIFY: begin
                if (acc_a == acc_b)
                    state_d = EXECUTE;
                else
                    state_d = DONE;
            end
            
            STORE: begin
                state_d = DONE;
            end
            
            ERROR: begin
                state_d = RECOVER;
            end
            
            RECOVER: begin
                state_d = IDLE;
            end
            
            DONE: begin
                done = 1'b1;
                state_d = IDLE;
            end
        endcase
    end
    
    // 状态寄存器
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state_q <= IDLE;
        else
            state_q <= state_d;
    end
    
    // 数据通路
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc_a <= 8'h0;
            acc_b <= 8'h0;
            accumulator <= 16'h0;
        end else begin
            case (state_q)
                LOAD_A:   acc_a <= cmd;
                LOAD_B:   acc_b <= cmd;
                EXECUTE:  accumulator <= {8'h0, acc_a} + {8'h0, acc_b};
                default: ;
            endcase
        end
    end
    
    assign result = accumulator;
endmodule


// =============================================================================
// 综合测试顶层
// =============================================================================
module comprehensive_test_top (
    input  logic clk,
    input  logic rst_n,
    input  logic [31:0] test_data,
    output logic [31:0] test_result
);
    // 实例化各个测试模块
    logic [7:0] basic_reg_out, comb_out, latch_out;
    logic [7:0] concat_high, concat_low, concat_swap;
    logic [7:0] priority_grant;
    logic [1:0] fsm_state;
    logic       fsm_busy;
    
    basic_registers basic_reg (
        .clk      (clk),
        .rst_n    (rst_n),
        .data_in  (test_data[7:0]),
        .data_out (basic_reg_out)
    );
    
    priority_encoder pri_enc (
        .req   (test_data[7:0]),
        .grant (priority_grant[2:0]),
        .valid ()
    );
    
    state_machine fsm (
        .clk      (clk),
        .rst_n    (rst_n),
        .start    (test_data[8]),
        .done     (test_data[9]),
        .state_out (fsm_state),
        .busy     (fsm_busy)
    );
    
    assign test_result = {24'h0, basic_reg_out};
endmodule
