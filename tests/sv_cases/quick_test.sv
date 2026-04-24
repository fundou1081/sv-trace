
module test_module (
    input clk,
    input rst_n,
    input [7:0] data_in,
    input valid,
    input ready,
    input [1:0] mode,
    output [7:0] data_out,
    output valid_out,
    output ready_out
);
    
    // 1. Clocked logic with if
    always @(posedge clk) begin
        if (!rst_n) begin
            data_out <= 0;
        end else if (valid) begin
            if (mode == 2'd0)
                data_out <= data_in + 1;
            else if (mode == 2'd1)
                data_out <= data_in - 1;
            else if (mode == 2'd2)
                data_out <= data_in + 2;
            else
                data_out <= data_in;
        end
    end
    
    // 2. Valid ready handshake
    always @(posedge clk) begin
        if (valid && ready)
            valid_out <= 1;
    end
    
    // 3. Continuous assignment
    assign ready_out = valid;
    
endmodule
