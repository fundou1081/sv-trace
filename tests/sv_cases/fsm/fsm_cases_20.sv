// ============================================================================
// FSMExtractor 测试用例 - 20个状态机语法组合
// ============================================================================

// 1. 二进制编码状态机
module fsm_01_binary_enc;
    parameter [1:0] IDLE = 2'b00, RUN = 2'b01, DONE = 2'b10;
    logic clk, rst_n;
    logic [1:0] state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= IDLE;
        else state <= next_state;
    
    always_comb
        case (state)
            IDLE: next_state = RUN;
            RUN: next_state = DONE;
            DONE: next_state = IDLE;
        endcase
endmodule

// 2. One-Hot 编码
module fsm_02_onehot_enc;
    parameter [3:0] IDLE = 4'b0001, RUN = 4'b0010, DONE = 4'b0100;
    logic clk, rst_n;
    logic [3:0] state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= IDLE;
        else state <= next_state;
    
    always_comb
        case (state)
            IDLE: next_state = RUN;
            RUN: next_state = DONE;
            DONE: next_state = IDLE;
        endcase
endmodule

// 3. Gray 编码
module fsm_03_gray_enc;
    parameter [1:0] IDLE = 2'b00, RUN = 2'b01, DONE = 2'b11;
    logic clk, rst_n;
    logic [1:0] state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= IDLE;
        else state <= next_state;
    
    always_comb
        case (state)
            IDLE: next_state = RUN;
            RUN: next_state = DONE;
            DONE: next_state = IDLE;
        endcase
endmodule

// 4. typedef enum 状态机
module fsm_04_typedef_enum;
    typedef enum logic [1:0] {IDLE, RUN, DONE} state_t;
    logic clk, rst_n;
    state_t state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= IDLE;
        else state <= next_state;
    
    always_comb
        case (state)
            IDLE: next_state = RUN;
            RUN: next_state = DONE;
            DONE: next_state = IDLE;
        endcase
endmodule

// 5. 单 always_ff 状态机 (无 next_state)
module fsm_05_single_always;
    logic clk, rst_n;
    logic [1:0] state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= 2'b00;
        else
            case (state)
                2'b00: state <= 2'b01;
                2'b01: state <= 2'b10;
                2'b10: state <= 2'b00;
            endcase
endmodule

// 6. 有复位状态的状态机
module fsm_06_with_reset_state;
    logic clk, rst_n;
    logic [2:0] state, next_state;
    parameter IDLE = 3'b001, INIT = 3'b010, RUN = 3'b100;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= IDLE;
        else state <= next_state;
    
    always_comb
        case (state)
            IDLE: next_state = INIT;
            INIT: next_state = RUN;
            RUN: next_state = IDLE;
        endcase
endmodule

// 7. 多输入条件状态机
module fsm_07_multi_input;
    logic clk, rst_n, start, stop, pause;
    logic [1:0] state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= 2'b00;
        else state <= next_state;
    
    always_comb begin
        case (state)
            2'b00: next_state = start ? 2'b01 : 2'b00;
            2'b01: next_state = stop ? 2'b10 : (pause ? 2'b01 : 2'b01);
            2'b10: next_state = 2'b00;
            default: next_state = 2'b00;
        endcase
    end
endmodule

// 8. 状态机带输出 (Moore)
module fsm_08_moore_output;
    logic clk, rst_n;
    logic [1:0] state, next_state;
    logic out_valid, out_error;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= 2'b00;
        else state <= next_state;
    
    always_comb begin
        case (state)
            2'b00: begin out_valid = 0; out_error = 0; next_state = 2'b01; end
            2'b01: begin out_valid = 1; out_error = 0; next_state = 2'b10; end
            2'b10: begin out_valid = 0; out_error = 1; next_state = 2'b00; end
            default: begin out_valid = 0; out_error = 0; next_state = 2'b00; end
        endcase
    end
endmodule

// 9. 状态机带 Mealy 输出
module fsm_09_mealy_output;
    logic clk, rst_n, go;
    logic [1:0] state, next_state;
    logic out;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= 2'b00;
        else state <= next_state;
    
    always_comb begin
        case (state)
            2'b00: begin out = 0; next_state = go ? 2'b01 : 2'b00; end
            2'b01: begin out = 1; next_state = 2'b00; end
            default: begin out = 0; next_state = 2'b00; end
        endcase
    end
endmodule

// 10. 状态机带计数器
module fsm_10_with_counter;
    logic clk, rst_n;
    logic [1:0] state, next_state;
    logic [3:0] cnt;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= 2'b00;
        else state <= next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) cnt <= 0;
        else if (state == 2'b01) cnt <= cnt + 1;
        else cnt <= 0;
    
    always_comb
        case (state)
            2'b00: next_state = 2'b01;
            2'b01: next_state = (cnt >= 10) ? 2'b10 : 2'b01;
            2'b10: next_state = 2'b00;
            default: next_state = 2'b00;
        endcase
endmodule

// 11. 嵌套状态机
module fsm_11_nested;
    logic clk, rst_n;
    logic [2:0] state, sub_state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) begin
            state <= 3'b001;
            sub_state <= 0;
        end else begin
            state <= next_state;
        end
    
    always_comb
        case (state)
            3'b001: next_state = 3'b010;
            3'b010: next_state = 3'b100;
            3'b100: next_state = 3'b001;
            default: next_state = 3'b001;
        endcase
endmodule

// 12. 状态机带握手
module fsm_12_handshake;
    logic clk, rst_n, req, ack;
    logic [1:0] state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= 2'b00;
        else state <= next_state;
    
    always_comb begin
        case (state)
            2'b00: next_state = req ? 2'b01 : 2'b00;
            2'b01: next_state = ack ? 2'b10 : 2'b01;
            2'b10: next_state = 2'b00;
            default: next_state = 2'b00;
        endcase
    end
endmodule

// 13. 状态机带 FIFO 接口
module fsm_13_fifo_if;
    logic clk, rst_n, wr_en, rd_en, full, empty;
    logic [7:0] data_in, data_out;
    logic [1:0] state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= 2'b00;
        else state <= next_state;
    
    always_comb begin
        case (state)
            2'b00: next_state = (!full && wr_en) ? 2'b01 : 2'b00;
            2'b01: next_state = (!empty && rd_en) ? 2'b10 : 2'b01;
            2'b10: next_state = 2'b00;
            default: next_state = 2'b00;
        endcase
    end
endmodule

// 14. 状态机带 AXI 接口
module fsm_14_axi_like;
    logic clk, rst_n, aw_valid, aw_ready, w_valid, w_ready, b_valid;
    logic [1:0] state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= 2'b00;
        else state <= next_state;
    
    always_comb begin
        case (state)
            2'b00: next_state = aw_valid ? 2'b01 : 2'b00;
            2'b01: next_state = w_valid ? 2'b10 : 2'b01;
            2'b10: next_state = b_valid ? 2'b00 : 2'b10;
            default: next_state = 2'b00;
        endcase
    end
endmodule

// 15. 状态机带优先级编码
module fsm_15_priority_enc;
    logic clk, rst_n;
    logic a, b, c, d;
    logic [2:0] state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= 3'b001;
        else state <= next_state;
    
    always_comb begin
        if (a) next_state = 3'b010;
        else if (b) next_state = 3'b100;
        else if (c) next_state = 3'b001;
        else next_state = 3'b001;
    end
endmodule

// 16. 状态机带 default 状态
module fsm_16_with_default;
    logic clk, rst_n;
    logic [2:0] state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= 3'b001;
        else state <= next_state;
    
    always_comb
        case (state)
            3'b001: next_state = 3'b010;
            3'b010: next_state = 3'b100;
            3'b100: next_state = 3'b001;
            default: next_state = 3'b001;
        endcase
endmodule

// 17. 无 default 状态机 (测试边缘情况)
module fsm_17_no_default;
    logic clk, rst_n;
    logic [1:0] state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= 2'b00;
        else state <= next_state;
    
    always_comb
        case (state)
            2'b00: next_state = 2'b01;
            2'b01: next_state = 2'b10;
            // 没有 default
        endcase
endmodule

// 18. 带命名的 state 变量
module fsm_18_named_var;
    logic clk, rst_n;
    logic [1:0] fsm_state, fsm_next;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) fsm_state <= 2'b00;
        else fsm_state <= fsm_next;
    
    always_comb
        case (fsm_state)
            2'b00: fsm_next = 2'b01;
            2'b01: fsm_next = 2'b10;
            2'b10: fsm_next = 2'b00;
        endcase
endmodule

// 19. 多 bit 状态变量
module fsm_19_wide_state;
    logic clk, rst_n;
    logic [7:0] state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= 8'h01;
        else state <= next_state;
    
    always_comb
        case (state)
            8'h01: next_state = 8'h02;
            8'h02: next_state = 8'h04;
            8'h04: next_state = 8'h01;
            default: next_state = 8'h01;
        endcase
endmodule

// 20. 状态机带边界检测
module fsm_20_boundary;
    logic clk, rst_n;
    logic [3:0] threshold;
    logic [1:0] state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= 2'b00;
        else state <= next_state;
    
    always_comb begin
        case (state)
            2'b00: next_state = (threshold > 0) ? 2'b01 : 2'b00;
            2'b01: next_state = (threshold >= 8) ? 2'b10 : 2'b01;
            2'b10: next_state = 2'b00;
            default: next_state = 2'b00;
        endcase
    end
endmodule
