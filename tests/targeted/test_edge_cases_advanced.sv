// ============================================================================
// Advanced Edge Cases - 高级Corner Case
// ============================================================================

// Test 1: 跨时钟域边界条件
module cdc_boundary_conditions;
    // 快到慢时钟
    logic fast_clk, slow_clk;
    logic fast_rst_n, slow_rst_n;
    logic [7:0] fast_data, slow_data;
    logic fast_valid;
    
    // 快时钟域
    always_ff @(posedge fast_clk or negedge fast_rst_n) begin
        if (!fast_rst_n)
            fast_data <= 8'h00;
        else
            fast_data <= fast_data + 1;
    end
    
    // 握手同步
    logic req, ack;
    logic [1:0] req_sync, ack_sync;
    
    always_ff @(posedge fast_clk or negedge fast_rst_n) begin
        if (!fast_rst_n)
            req_sync <= 2'b00;
        else
            req_sync <= {req_sync[0], req};
    end
    
    always_ff @(posedge slow_clk or negedge slow_rst_n) begin
        if (!slow_rst_n)
            ack_sync <= 2'b00;
        else
            ack_sync <= {ack_sync[0], ack};
    end
    
    // 同步后的请求检测上升沿
    logic req_re, ack_re;
    logic req_re_d, ack_re_d;
    
    always_ff @(posedge slow_clk or negedge slow_rst_n) begin
        if (!slow_rst_n) begin
            req_re_d <= 1'b0;
            req_re <= 1'b0;
        end else begin
            req_re_d <= req_sync[1];
            req_re <= req_sync[1] && !req_re_d;
        end
    end
    
    always_ff @(posedge fast_clk or negedge fast_rst_n) begin
        if (!fast_rst_n) begin
            ack_re_d <= 1'b0;
            ack_re <= 1'b0;
        end else begin
            ack_re_d <= ack_sync[1];
            ack_re <= ack_sync[1] && !ack_re_d;
        end
    end
endmodule


// Test 2: 多时钟域握手
module multi_domain_handshake #(
    parameter int NUM_DOMAINS = 3
) (
    input  logic [NUM_DOMAINS-1:0] clks,
    input  logic [NUM_DOMAINS-1:0] rsts_n,
    input  logic req_domain0,
    output logic [NUM_DOMAINS-1:0] acks
);
    genvar i;
    
    for (genvar i = 0; i < NUM_DOMAINS; i++) begin : gen_domain_sync
        logic req_sync, req_meta, req_sync2;
        logic [2:0] ack_sync_chain;
        
        // 请求同步到目标域
        if (i == 0) begin : gen_req_src
            assign req_sync = req_domain0;
        end else begin : gen_req_sync
            always_ff @(posedge clks[i] or negedge rsts_n[i]) begin
                if (!rsts_n[i]) begin
                    req_meta <= 1'b0;
                    req_sync2 <= 1'b0;
                end else begin
                    req_meta <= req_sync;
                    req_sync2 <= req_meta;
                end
            end
        end
        
        // Ack同步回源域
        always_ff @(posedge clks[0] or negedge rsts_n[0]) begin
            if (!rsts_n[0]) begin
                ack_sync_chain <= '0;
            end else begin
                ack_sync_chain <= {ack_sync_chain[1:0], acks[i]};
            end
        end
    end
endmodule


// Test 3: 复位域交叉
module reset_domain_cross;
    logic clk_a, clk_b;
    logic rst_a_n, rst_b_n;
    logic rst_a_internal, rst_b_internal;
    
    // 外部复位同步
    logic [2:0] rst_a_sync, rst_b_sync;
    
    always_ff @(posedge clk_a or negedge rst_a_n) begin
        if (!rst_a_n)
            rst_a_sync <= '0;
        else
            rst_a_sync <= {rst_a_sync[1:0], 1'b1};
    end
    
    assign rst_a_internal = rst_a_sync[2];
    
    always_ff @(posedge clk_b or negedge rst_b_n) begin
        if (!rst_b_n)
            rst_b_sync <= '0;
        else
            rst_b_sync <= {rst_b_sync[1:0], 1'b1};
    end
    
    assign rst_b_internal = rst_b_sync[2];
    
    // 复位释放时序问题
    logic [7:0] reg_a, reg_b;
    
    always_ff @(posedge clk_a or negedge rst_a_internal) begin
        if (!rst_a_internal)
            reg_a <= 8'h00;
        else
            reg_a <= reg_a + 1;
    end
    
    // reg_b依赖reg_a的初始值
    always_ff @(posedge clk_b or negedge rst_b_internal) begin
        if (!rst_b_internal)
            reg_b <= 8'h00;
        else
            reg_b <= reg_a;  // 跨域传递，可能有时序问题
    end
endmodule


// Test 4: 复杂条件表达式
module complex_conditions;
    logic [7:0] a, b, c, d;
    logic [2:0] sel1, sel2;
    logic cond1, cond2, cond3;
    logic [7:0] result;
    
    // 嵌套三元表达式
    always_comb begin
        result = (cond1 && cond2) ? a :
                 (!cond1 && cond3) ? b :
                 (cond1 && !cond2) ? c : d;
    end
    
    // 多条件组合
    always_comb begin
        if ({cond1, cond2, cond3} == 3'b111)
            result = a;
        else if ({cond1, cond2, cond3} == 3'b000)
            result = b;
        else if (cond1 ^ cond2 ^ cond3)
            result = c;
        else
            result = d;
    end
    
    // 移位后比较
    logic [7:0] shift_result;
    logic [2:0] shift_amount;
    
    always_comb begin
        shift_result = a << shift_amount;
        result = (shift_result > 8'h80) ? 8'hFF : 8'h00;
    end
endmodule


// Test 5: 生成块中的条件
module generate_conditions #(
    parameter int WIDTH = 32,
    parameter int N = 8
) (
    input  logic clk,
    input  logic rst_n,
    input  logic [N-1:0][WIDTH-1:0] data_in,
    output logic [N-1:0][WIDTH-1:0] data_out
);
    genvar i;
    
    // 条件生成
    for (i = 0; i < N; i++) begin : gen_pipeline
        logic [WIDTH-1:0] pipeline_reg;
        
        // 第一个寄存器无条件
        if (i == 0) begin : gen_first
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    pipeline_reg <= '0;
                else
                    pipeline_reg <= data_in[i];
            end
        end
        
        // 中间寄存器有条件使能
        if (i > 0 && i < N-1) begin : gen_middle
            logic enable;
            assign enable = data_in[i][0];  // LSB作为使能
            
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    pipeline_reg <= '0;
                else if (enable)
                    pipeline_reg <= data_in[i];
            end
        end
        
        // 最后一个寄存器
        if (i == N-1) begin : gen_last
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    pipeline_reg <= '0;
                else
                    pipeline_reg <= data_in[i];
            end
        end
        
        assign data_out[i] = pipeline_reg;
    end
endmodule


// Test 6: 多维数组访问
module multi_dim_array;
    logic clk;
    logic [7:0] mem [0:255][0:7];  // 2D memory
    logic [7:0] result1, result2;
    logic [15:0] addr1, addr2;
    logic [2:0] sub_addr;
    
    // 写入
    always_ff @(posedge clk) begin
        mem[addr1][sub_addr] <= result1;
    end
    
    // 读取
    assign result2 = mem[addr2][sub_addr];
    
    // 突发访问
    logic [7:0] burst_data [0:3];
    logic [1:0] burst_offset;
    
    always_comb begin
        for (int i = 0; i < 4; i++) begin
            burst_data[i] = mem[addr1 + i][sub_addr];
        end
    end
endmodule


// Test 7: 函数和任务
module function_task_examples;
    // 带返回值的函数
    function logic [7:0] mul_add (
        input logic [7:0] a, b, c
    );
        mul_add = (a * b) + c;
    endfunction
    
    // 自动函数(可递归)
    function automatic logic [31:0] factorial (
        input logic [31:0] n
    );
        if (n <= 1)
            factorial = 1;
        else
            factorial = n * factorial(n - 1);
    endfunction
    
    // 任务
    task wait_cycles (
        input int cycles
    );
        repeat (cycles) @(posedge clk);
    endtask
    
    // 使用
    logic [7:0] a, b, c;
    logic [7:0] result_func;
    logic [31:0] fact_result;
    
    always_comb begin
        result_func = mul_add(a, b, c);
    end
    
    // 综合不支持递归
    // fact_result = factorial(5);
endmodule


// Test 8: 接口和modport
interface simple_bus (
    input logic clk
);
    logic [7:0] addr;
    logic [7:0] data;
    logic wr_en, rd_en;
    
    modport master (
        output addr, data, wr_en, rd_en,
        input clk
    );
    
    modport slave (
        input addr, data, wr_en, rd_en,
        output data
    );
endinterface

module bus_master (
    simple_bus.master bus_if
);
    always_ff @(posedge bus_if.clk) begin
        if (bus_if.wr_en)
            bus_if.addr <= bus_if.addr + 1;
    end
endmodule

module bus_slave (
    simple_bus.slave bus_if
);
    logic [7:0] internal_regs [0:15];
    
    always_ff @(posedge bus_if.clk) begin
        if (bus_if.wr_en)
            internal_regs[bus_if.addr] <= bus_if.data;
    end
endmodule


// Test 9: 断言和假设
module assertions_examples (
    input logic clk,
    input logic rst_n,
    input logic [7:0] data,
    input logic valid
);
    // 序列
    sequence data_valid_seq;
        valid && (data != 8'hXX);
    endsequence
    
    // 属性
    property data_not_x;
        @(posedge clk) disable iff (!rst_n)
        valid |-> (data != 8'hXX);
    endproperty
    
    // 断言
    assert property (data_not_x)
        else $error("Data contains X!");
    
    // 覆盖
    cover property (@(posedge clk) valid);
endmodule


// Test 10: 别名和强制驱动
module alias_force;
    logic a, b, c;
    logic [3:0] sel;
    logic enable;
    
    // 别名 - 同一个信号多个名字
    wire alias_a = a;
    assign b = a;  // b is alias of a
    
    // 强制驱动
    initial begin
        force c = 1'b0;
        #10;
        release c;
    end
    
    // 条件强制
    always_comb begin
        if (enable)
            force a = 1'b0;
        else
            release a;
    end
endmodule
