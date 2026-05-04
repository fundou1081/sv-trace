// Test 8: Complex FSM with datapath
module complex_fsm (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] cmd,
    input  logic       cmd_valid,
    output logic [15:0] result,
    output logic        done
);
    typedef enum logic [3:0] {
        IDLE   = 4'h0,
        DECODE = 4'h1,
        LOAD_A = 4'h2,
        LOAD_B = 4'h3,
        EXEC   = 4'h4,
        STORE  = 4'h5,
        DONE   = 4'h6
    } state_t;
    
    state_t state_q, state_d;
    logic [7:0] acc_a, acc_b;
    logic [15:0] accumulator;
    
    // State transition
    always_comb begin
        state_d = state_q;
        done = 1'b0;
        
        case (state_q)
            IDLE:   if (cmd_valid) state_d = DECODE;
            DECODE: case (cmd[1:0])
                        2'b00: state_d = LOAD_A;
                        2'b01: state_d = LOAD_B;
                        2'b10: state_d = EXEC;
                        default: state_d = IDLE;
                    endcase
            LOAD_A: state_d = EXEC;
            LOAD_B: state_d = EXEC;
            EXEC:   state_d = STORE;
            STORE:  state_d = DONE;
            DONE: begin
                done = 1'b1;
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
    
    // Datapath
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc_a <= 8'h0;
            acc_b <= 8'h0;
            accumulator <= 16'h0;
        end else begin
            case (state_q)
                LOAD_A: acc_a <= cmd;
                LOAD_B: acc_b <= cmd;
                EXEC:   accumulator <= {8'h0, acc_a} + {8'h0, acc_b};
                default: ;
            endcase
        end
    end
    
    assign result = accumulator;
endmodule
