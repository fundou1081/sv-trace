// Test 4: Generate for - Multiple registers
module generate_regs (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] data_in,
    output logic [7:0] reg_a,
    output logic [7:0] reg_b,
    output logic [7:0] reg_c
);
    // Generate multiple registers
    generate
        genvar i;
        for (i = 0; i < 3; i++) begin : gen_regs
            // This is a simplified version
        end
    endgenerate
    
    // Direct register instantiation
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            reg_a <= 8'h00;
        else
            reg_a <= data_in;
    end
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            reg_b <= 8'h00;
        else
            reg_b <= reg_a;
    end
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            reg_c <= 8'h00;
        else
            reg_c <= reg_b;
    end
endmodule
