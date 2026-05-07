// ============================================================================
// FSMExtractor 测试用例 - 状态机
// ============================================================================

// 简单状态机
module fsm_simple(
    input clk,
    input rst_n,
    input start
);
    typedef enum logic [1:0] {
        IDLE = 2'b00,
        RUN  = 2'b01,
        DONE = 2'b10
    } state_t;
    
    state_t state, next_state;
    
    // 状态寄存器
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end
    
    // 状态转换逻辑
    always_comb begin
        case (state)
            IDLE: next_state = start ? RUN : IDLE;
            RUN:  next_state = DONE;
            DONE: next_state = IDLE;
            default: next_state = IDLE;
        endcase
    end
endmodule

// 交通灯状态机
module traffic_light(
    input clk,
    input rst_n,
    input sensor
);
    typedef enum logic [2:0] {
        RED    = 3'b001,
        YELLOW = 3'b010,
        GREEN  = 3'b100
    } light_t;
    
    light_t state, next_state;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= RED;
        else
            state <= next_state;
    end
    
    always_comb begin
        case (state)
            RED:    next_state = sensor ? GREEN : RED;
            GREEN:  next_state = YELLOW;
            YELLOW: next_state = RED;
        endcase
    end
endmodule

// 单 always_ff 状态机 (无 next_state)
module fsm_single_always(
    input clk,
    input rst_n
);
    logic [1:0] state;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= 2'b00;
        else
            case (state)
                2'b00: state <= 2'b01;
                2'b01: state <= 2'b10;
                2'b10: state <= 2'b00;
            endcase
    end
endmodule
