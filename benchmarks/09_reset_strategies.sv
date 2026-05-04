// Test 9: Reset strategies
module reset_strategies (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] async_data,
    output logic [7:0] sync_out,
    output logic [7:0] async_out,
    output logic [7:0] multi_rst_out
);
    // Synchronous reset
    always_ff @(posedge clk) begin
        if (!rst_n)
            sync_out <= 8'h00;
        else
            sync_out <= async_data;
    end
    
    // Asynchronous reset
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            async_out <= 8'h00;
        else
            async_out <= async_data;
    end
    
    // Multi-level reset
    logic init_done, warm_rst;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            multi_rst_out <= 8'h00;
        else if (!init_done)
            multi_rst_out <= 8'hAA;
        else if (warm_rst)
            multi_rst_out <= 8'h55;
        else
            multi_rst_out <= async_data;
    end
endmodule
