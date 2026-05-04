// Test 10: Pipeline registers with stall
module pipeline_registers (
    input  logic clk,
    input  logic rst_n,
    input  logic [31:0] data_in,
    input  logic        valid_in,
    input  logic        stall,
    output logic [31:0] data_out,
    output logic         valid_out
);
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
