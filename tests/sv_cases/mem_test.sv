
module top(
    input clk,
    input [7:0] wr_data,
    input [3:0] wr_addr,
    input wr_en,
    input [3:0] rd_addr,
    output [7:0] rd_data
);
    
    // Memory
    reg [7:0] mem [0:15];
    
    // Write
    always @(posedge clk) begin
        if (wr_en)
            mem[wr_addr] <= wr_data;
    end
    
    // Read (从memory读取)
    always @(posedge clk) begin
        rd_data <= mem[rd_addr];
    end
    
    // 加上一些处理逻辑
    reg [7:0] temp;
    always @(posedge clk) begin
        temp <= rd_data + 1;  // 对读取值加工
    end
endmodule
