
module advanced_top (
    input clk, rst_n,
    input [7:0] data_in0,      // 输入0
    input [7:0] data_in1,      // 输入1  
    input valid,                 // 有效信号
    input [2:0] mode,           // 模式选择
    output [7:0] result,        // 结果输出
    output result_valid        // 结果有效
);
    
    // 内部信号
    reg [7:0] stage1_data;
    reg [7:0] stage2_data;
    
    // Stage 1: data_in0 + data_in1 * mode
    always @(posedge clk) begin
        if (!rst_n) begin
            stage1_data <= 0;
        end else if (valid) begin
            case (mode)
                3'd0: stage1_data <= data_in0 + data_in1;
                3'd1: stage1_data <= data_in0 - data_in1;
                3'd2: stage1_data <= data_in0 & data_in1;
                3'd3: stage1_data <= data_in0 | data_in1;
                default: stage1_data <= data_in0;
            endcase
        end
    end
    
    // Stage 2: stage1 + 1
    always @(posedge clk) begin
        if (!rst_n) begin
            stage2_data <= 0;
            result_valid <= 0;
        end else begin
            stage2_data <= stage1_data + 1;
            result_valid <= valid;
        end
    end
    
    // Output
    assign result = stage2_data;
endmodule
