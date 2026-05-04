// Test 1: Basic always_ff registers
module basic_registers (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data_out <= 8'h00;
        else
            data_out <= data_in;
    end
endmodule
