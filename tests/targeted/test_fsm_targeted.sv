// ============================================================================
// FSM Targeted Test Cases - 状态机专项测试
// ============================================================================

// Test 1: 标准状态机 (typedef enum)
module fsm_enum_test;
    typedef enum logic [2:0] {
        IDLE    = 3'b000,
        START   = 3'b001,
        RUN     = 3'b010,
        WAIT    = 3'b011,
        STOP    = 3'b100,
        ERROR   = 3'b111
    } state_t;
    
    state_t state, next_state;
    logic clk, rst_n;
    logic [7:0] data;
    logic valid;
    
    // 状态转移逻辑
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end
    
    // 下一状态逻辑
    always_comb begin
        next_state = state;
        case (state)
            IDLE:   if (valid) next_state = START;
            START:  next_state = RUN;
            RUN:    if (data == 8'hFF) next_state = WAIT;
            WAIT:   next_state = STOP;
            STOP:   next_state = IDLE;
            ERROR:  next_state = IDLE;
            default: next_state = ERROR;
        endcase
    end
endmodule


// Test 2: 状态机 (parameter编码)
module fsm_param_test;
    parameter IDLE = 2'b00;
    parameter S1   = 2'b01;
    parameter S2   = 2'b10;
    parameter S3   = 2'b11;
    
    logic [1:0] state;
    logic clk, rst_n;
    logic enable;
    
    always_ff @(posedge clk) begin
        if (!rst_n)
            state <= IDLE;
        else begin
            case (state)
                IDLE: if (enable) state <= S1;
                S1:   state <= S2;
                S2:   state <= S3;
                S3:   state <= IDLE;
            endcase
        end
    end
endmodule


// Test 3: 单状态状态机
module fsm_single_state;
    logic clk, rst_n;
    logic [7:0] counter;
    
    always_ff @(posedge clk) begin
        if (!rst_n)
            counter <= 0;
        else
            counter <= counter + 1;
    end
endmodule


// Test 4: 深层嵌套状态机
module fsm_deep_nested;
    typedef enum logic [3:0] {
        S0, S1, S2, S3, S4, S5, S6, S7,
        S8, S9, S10, S11, S12, S13, S14, S15
    } state_t;
    
    state_t state;
    logic clk, rst_n;
    
    always_ff @(posedge clk) begin
        if (!rst_n)
            state <= S0;
        else begin
            case (state)
                S0:  state <= S1;
                S1:  state <= S2;
                S2:  state <= S3;
                S3:  state <= S4;
                S4:  state <= S5;
                S5:  state <= S6;
                S6:  state <= S7;
                S7:  state <= S8;
                S8:  state <= S9;
                S9:  state <= S10;
                S10: state <= S11;
                S11: state <= S12;
                S12: state <= S13;
                S13: state <= S14;
                S14: state <= S15;
                S15: state <= S0;
            endcase
        end
    end
endmodule
