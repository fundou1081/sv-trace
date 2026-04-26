// ============================================================================
// Fanout/Fanin Targeted Test Cases - 扇出扇入专项测试
// ============================================================================

module fanout_test_high;
    // 高扇出信号 - 时钟和复位
    logic clk;
    logic rst_n;
    
    // 高扇出使能信号 - 驱动多个寄存器
    logic enable;
    
    // 大量寄存器
    logic [7:0] data0, data1, data2, data3, data4;
    logic [7:0] data5, data6, data7, data8, data9;
    logic [7:0] data10, data11, data12, data13, data14;
    logic [7:0] data15, data16, data17, data18, data19;
    
    // 每个寄存器都受enable控制
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data0  <= 0;
            data1  <= 0;
            data2  <= 0;
            data3  <= 0;
            data4  <= 0;
            data5  <= 0;
            data6  <= 0;
            data7  <= 0;
            data8  <= 0;
            data9  <= 0;
            data10 <= 0;
            data11 <= 0;
            data12 <= 0;
            data13 <= 0;
            data14 <= 0;
            data15 <= 0;
            data16 <= 0;
            data17 <= 0;
            data18 <= 0;
            data19 <= 0;
        end else if (enable) begin
            data0  <= data0 + 1;
            data1  <= data1 + 1;
            data2  <= data2 + 1;
            data3  <= data3 + 1;
            data4  <= data4 + 1;
            data5  <= data5 + 1;
            data6  <= data6 + 1;
            data7  <= data7 + 1;
            data8  <= data8 + 1;
            data9  <= data9 + 1;
            data10 <= data10 + 1;
            data11 <= data11 + 1;
            data12 <= data12 + 1;
            data13 <= data13 + 1;
            data14 <= data14 + 1;
            data15 <= data15 + 1;
            data16 <= data16 + 1;
            data17 <= data17 + 1;
            data18 <= data18 + 1;
            data19 <= data19 + 1;
        end
    end
endmodule


module fanout_test_low;
    // 低扇出信号
    logic clk;
    logic rst_n;
    logic enable;
    
    // 只有少数几个信号
    logic [7:0] internal_sig1, internal_sig2;
    logic flag1, flag2, flag3;
    
    // internal_sig1 扇出为3
    always_ff @(posedge clk) begin
        if (enable) begin
            internal_sig1 <= internal_sig1 + 1;
            internal_sig2 <= internal_sig2 - 1;
        end
    end
    
    // flag1, flag2 各扇出为1
    always_ff @(posedge clk) begin
        flag1 <= internal_sig1[0];
        flag2 <= internal_sig2[0];
        flag3 <= flag1 ^ flag2;
    end
endmodule


module fanout_test_chain;
    // 链式扇出 - 每级扇出为1
    logic clk;
    logic data_in;
    logic stage1, stage2, stage3, stage4, stage5;
    
    always_ff @(posedge clk) begin
        stage1 <= data_in;
        stage2 <= stage1;
        stage3 <= stage2;
        stage4 <= stage3;
        stage5 <= stage4;
    end
endmodule


module fanout_test_converge;
    // 收敛结构 - 多入一出
    logic clk;
    logic a, b, c, d;
    logic result;
    
    logic mid1, mid2;
    
    always_ff @(posedge clk) begin
        mid1 <= a && b;
        mid2 <= c && d;
        result <= mid1 && mid2;
    end
endmodule
