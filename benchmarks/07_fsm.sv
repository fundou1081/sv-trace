// Test 7: FSM - State machine
module state_machine (
    input  logic clk,
    input  logic rst_n,
    input  logic start,
    input  logic done,
    output logic [1:0] state_out,
    output logic       busy
);
    typedef enum logic [1:0] {
        IDLE  = 2'b00,
        RUN   = 2'b01,
        WAIT  = 2'b10,
        DONE  = 2'b11
    } state_t;
    
    state_t state_q, state_d;
    
    // Next state logic
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
    
    // State register
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state_q <= IDLE;
        else
            state_q <= state_d;
    end
    
    assign state_out = state_q;
endmodule
