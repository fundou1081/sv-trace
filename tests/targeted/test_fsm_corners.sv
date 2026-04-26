// ============================================================================
// FSM Corner Cases - 状态机边界测试
// ============================================================================

// Test 1: One-hot编码状态机
module fsm_onehot;
    // One-hot编码: 16状态需要16位
    localparam [15:0] S0  = 16'b0000000000000001;
    localparam [15:0] S1  = 16'b0000000000000010;
    localparam [15:0] S2  = 16'b0000000000000100;
    localparam [15:0] S3  = 16'b0000000000001000;
    localparam [15:0] S4  = 16'b0000000000010000;
    localparam [15:0] S5  = 16'b0000000000100000;
    localparam [15:0] S6  = 16'b0000000001000000;
    localparam [15:0] S7  = 16'b0000000010000000;
    localparam [15:0] S8  = 16'b0000000100000000;
    localparam [15:0] S9  = 16'b0000001000000000;
    localparam [15:0] S10 = 16'b0000010000000000;
    localparam [15:0] S11 = 16'b0000100000000000;
    localparam [15:0] S12 = 16'b0001000000000000;
    localparam [15:0] S13 = 16'b0010000000000000;
    localparam [15:0] S14 = 16'b0100000000000000;
    localparam [15:0] S15 = 16'b1000000000000000;
    
    (* syn_encoding = "onehot" *)
    logic [15:0] state;
    logic clk, rst_n;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S0;
        else begin
            case (1'b1)
                state[S0]: if (start) state <= S1;
                state[S1]: state <= S2;
                state[S2]: state <= S3;
                state[S3]: state <= S4;
                state[S4]: state <= S5;
                state[S5]: state <= S6;
                state[S6]: state <= S7;
                state[S7]: state <= S8;
                state[S8]: state <= S9;
                state[S9]: state <= S10;
                state[S10]: state <= S11;
                state[S11]: state <= S12;
                state[S12]: state <= S13;
                state[S13]: state <= S14;
                state[S14]: state <= S15;
                state[S15]: state <= S0;
                default: state <= S0;
            endcase
        end
    end
endmodule


// Test 2: 三段式状态机
module fsm_three_seg;
    typedef enum logic [1:0] {
        IDLE,
        RUN,
        WAIT,
        DONE
    } state_t;
    
    state_t state_next, state_current;
    logic clk, rst_n;
    logic start, done;
    
    // 段1: 同步状态更新
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state_current <= IDLE;
        else
            state_current <= state_next;
    end
    
    // 段2: 下一状态逻辑
    always_comb begin
        state_next = state_current;
        case (state_current)
            IDLE: if (start) state_next = RUN;
            RUN:  if (done) state_next = WAIT;
            WAIT: state_next = DONE;
            DONE: state_next = IDLE;
        endcase
    end
    
    // 段3: 输出逻辑
    logic busy, complete;
    always_comb begin
        busy = (state_current == RUN);
        complete = (state_current == DONE);
    end
endmodule


// Test 3: 多状态机(一个模块两个FSM)
module fsm_multi;
    typedef enum logic [1:0] {
        FIDLE, FSTART, FRUN
    } fsm_state_t;
    
    typedef enum logic [1:0] {
        SIDLE, SREQ, SACK
    } sub_state_t;
    
    fsm_state_t fsm_state;
    sub_state_t sub_state;
    logic clk, rst_n;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fsm_state <= FIDLE;
            sub_state <= SIDLE;
        end else begin
            // FSM1
            case (fsm_state)
                FIDLE: fsm_state <= FSTART;
                FSTART: fsm_state <= FRUN;
                FRUN: fsm_state <= FIDLE;
            endcase
            
            // FSM2
            case (sub_state)
                SIDLE: sub_state <= SREQ;
                SREQ: sub_state <= SACK;
                SACK: sub_state <= SIDLE;
            endcase
        end
    end
endmodule


// Test 4: 复杂跳转条件
module fsm_complex_cond;
    typedef enum logic [2:0] {
        IDLE, RUN, WAIT, ERROR, RETRY, DONE
    } state_t;
    
    state_t state;
    logic clk, rst_n;
    logic [7:0] counter;
    logic overflow, underflow, parity_err;
    logic [3:0] mode;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else begin
            case (state)
                IDLE: 
                    if (mode == 4'b0001 && !parity_err)
                        state <= RUN;
                    else if (mode == 4'b0010)
                        state <= WAIT;
                
                RUN:
                    if (overflow || underflow)
                        state <= ERROR;
                    else if (counter == 8'hFF && mode[0])
                        state <= RETRY;
                    else if (counter >= 8'h10 && counter <= 8'hF0)
                        state <= DONE;
                
                WAIT:
                    if (counter > 8'h00)
                        state <= RUN;
                    else
                        state <= IDLE;
                
                ERROR:
                    if (parity_err && mode[3])
                        state <= RETRY;
                    else
                        state <= IDLE;
                
                RETRY:
                    state <= RUN;
                
                DONE:
                    state <= IDLE;
                
                default:
                    state <= IDLE;
            endcase
        end
    end
endmodule


// Test 5: 非法状态自恢复
module fsm_illegal_recover;
    typedef enum logic [2:0] {
        S0, S1, S2, S3, S4, S5, S6, S7
    } state_t;
    
    state_t state;
    logic clk, rst_n;
    
    // 3位状态可以表示8个状态，但我们只用了前5个
    // 后3个是"非法状态"
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S0;
        else begin
            case (state)
                S0: state <= S1;
                S1: state <= S2;
                S2: state <= S3;
                S3: state <= S4;
                S4: state <= S0;
                // 非法状态应该回到S0
                default: state <= S0;
            endcase
        end
    end
endmodule


// Test 6: 状态机含内部计数器
module fsm_with_counter;
    typedef enum logic [1:0] {
        IDLE, COUNT, DONE
    } state_t;
    
    state_t state;
    logic clk, rst_n;
    logic start;
    logic [7:0] count;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            count <= 0;
        end else begin
            case (state)
                IDLE: begin
                    count <= 0;
                    if (start)
                        state <= COUNT;
                end
                
                COUNT: begin
                    if (count >= 100) begin
                        state <= DONE;
                        count <= 0;
                    end else begin
                        count <= count + 1;
                    end
                end
                
                DONE: begin
                    state <= IDLE;
                end
            endcase
        end
    end
endmodule
