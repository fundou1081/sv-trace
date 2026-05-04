// Test 6: case statement - instruction decoder
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
        
        casez (instruction[6:0])
            7'b0000011: is_load = 1'b1;    // load
            7'b0100011: is_store = 1'b1;   // store
            7'b1100011: is_branch = 1'b1;  // branch
            7'b0110011: is_arith = 1'b1;   // arithmetic
            default: ;  // no operation
        endcase
    end
endmodule
