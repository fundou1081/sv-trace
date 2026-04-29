// ============================================================================
// Generate 块测试用例
// ============================================================================

// Test 1: for generate
module gen_for;
    wire [7:0] out [3:0];
    wire [7:0] in [3:0];
    
    genvar i;
    generate
        for (i = 0; i < 4; i = i + 1) begin : gen_block
            assign out[i] = in[i];
        end
    endgenerate
endmodule

// Test 2: if generate
module gen_if;
    parameter USE_FIFO = 1;
    
    generate
        if (USE_FIFO == 1) begin : fifo_gen
            wire [7:0] fifo_out;
        end else begin : ram_gen
            wire [7:0] ram_out;
        end
    endgenerate
endmodule

// Test 3: case generate
module gen_case;
    parameter MODE = 2;
    
    generate
        case (MODE)
            0: begin : mode_0
                wire [7:0] mode0_out;
            end
            1: begin : mode_1
                wire [7:0] mode1_out;
            end
            default: begin : mode_default
                wire [7:0] mode_default_out;
            end
        endcase
    endgenerate
endmodule
