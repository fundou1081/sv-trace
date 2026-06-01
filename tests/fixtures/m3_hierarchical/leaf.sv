// leaf.sv: 最底层模块
module leaf (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] din,
    output logic [7:0] dout
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            dout <= 8'h0;
        else
            dout <= din;
    end
endmodule
