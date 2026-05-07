// ============================================================================
// Driver 语法覆盖度 - 单模块测试文件 (修复版)
// 每个语法单独一个文件，确保提取结果正确
// ============================================================================

// 1. posedge 时钟
module test_01_posedge;
    logic clk;
    logic [7:0] data;
    always_ff @(posedge clk) begin
        data <= data + 1;
    end
endmodule

// 2. 异步复位 or negedge
module test_02_async_reset;
    logic clk, rst_n;
    logic [7:0] data;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) data <= 8'h0;
        else data <= data + 1;
    end
endmodule

// 3. 同步复位 if(rst)
module test_03_sync_reset_high;
    logic clk, rst;
    logic [7:0] data;
    always_ff @(posedge clk) begin
        if (rst) data <= 8'h0;
        else data <= data + 1;
    end
endmodule

// 4. 同步复位 if(!rst_n) 
module test_04_sync_reset_low;
    logic clk, rst_n;
    logic [7:0] data;
    always_ff @(posedge clk) begin
        if (!rst_n) data <= 8'h0;
        else data <= data + 1;
    end
endmodule

// 5. generate for
module test_05_generate_for;
    logic clk, rst_n;
    logic [7:0] data [0:3];
    genvar i;
    generate
        for (i = 0; i < 4; i = i + 1) begin : gen
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n) data[i] <= 8'h0;
                else data[i] <= i;
            end
        end
    endgenerate
endmodule

// 6. function return
module test_06_function;
    logic clk, rst;
    logic [7:0] data, result;
    function logic [7:0] calc(input logic [7:0] a);
        return a + 1;
    endfunction
    always_ff @(posedge clk) begin
        if (rst) result <= 8'h0;
        else result <= calc(data);
    end
endmodule
