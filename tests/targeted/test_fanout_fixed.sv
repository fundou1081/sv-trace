// ============================================================================
// Fanout Fixed Test - 修复扇出测试
// ============================================================================

module fanout_fixed;
    logic clk;
    logic rst_n;
    
    // Test: enable信号的真正扇出
    // enable被用于多个always块的条件判断
    logic enable;
    
    // 多个寄存器都根据enable更新
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data0 <= 8'b0;
        end else if (enable) begin
            data0 <= data0 + 1;
        end
    end
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data1 <= 8'b0;
        end else if (enable) begin
            data1 <= data1 - 1;
        end
    end
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data2 <= 8'b0;
        end else if (enable) begin
            data2 <= data2 + 2;
        end
    end
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data3 <= 8'b0;
        end else if (enable) begin
            data3 <= data3 - 2;
        end
    end
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data4 <= 8'b0;
        end else if (enable) begin
            data4 <= data4 + 4;
        end
    end
    
    // clk被多个always块使用
    always_ff @(posedge clk) begin
        clk_counter <= clk_counter + 1;
    end
    
    // rst_n被多个always块使用
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            rst_counter <= rst_counter + 1;
    end
    
    logic [7:0] data0, data1, data2, data3, data4;
    logic [15:0] clk_counter;
    logic [15:0] rst_counter;
endmodule
