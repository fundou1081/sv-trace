// ============================================================================
// DriverTracer 金标准测试 - 10个边界语法
// 期望：每个 module 至少提取到驱动信号和时钟/复位
// ============================================================================

// 1. Generate For with 时钟/复位
module driver_01_gen_for;
    logic clk, rst_n;
    logic [7:0] data [0:3];
    genvar i;
    generate
        for (i = 0; i < 4; i = i + 1) begin : gen_block
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n) data[i] <= 8'h0;
                else data[i] <= i;
            end
        end
    endgenerate
endmodule

// 2. Function Return
module driver_02_func_return;
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

// 3. Class Method with reset
module driver_03_class_method;
    logic clk, rst;
    logic [7:0] data_out;
    
    class DriverClass;
        randc logic [7:0] rand_data;
        function void drive_signal(output logic [7:0] d);
            d <= rand_data;
        endfunction
    endclass
    
    DriverClass drv;
    initial drv = new();
    
    always_ff @(posedge clk) begin
        if (!rst) data_out <= 8'h0;
        else drv.drive_signal(data_out);
    end
endmodule

// 4. Always Comb
module driver_04_always_comb;
    logic [7:0] a, b, c;
    always_comb begin
        c = a + b;
    end
endmodule

// 5. Continuous Assign
module driver_05_continuous;
    logic [7:0] a, b, c;
    assign c = a & b;
endmodule

// 6. Nested If with reset
module driver_06_nested_if;
    logic clk, rst;
    logic [7:0] data, sel;
    
    always_ff @(posedge clk) begin
        if (rst) data <= 8'h0;
        else if (sel > 8'd10) data <= 8'hFF;
        else if (sel > 8'd5) data <= 8'hAA;
        else data <= 8'h0;
    end
endmodule

// 7. Case with reset
module driver_07_case;
    logic clk, rst;
    logic [1:0] sel;
    logic [7:0] data;
    
    always_ff @(posedge clk) begin
        if (!rst) data <= 8'h0;
        else case (sel)
            2'b00: data <= 8'h00;
            2'b01: data <= 8'hFF;
            2'b10: data <= 8'hAA;
            default: data <= 8'h0;
        endcase
    end
endmodule

// 8. Multi-Driver (优先编码)
module driver_08_multi_driver;
    logic clk, rst;
    logic [7:0] data;
    
    always_ff @(posedge clk) begin
        if (rst) data <= 8'h0;
        else data <= data + 1;
    end
    
    always_ff @(posedge clk) begin
        data <= data + 2;
    end
endmodule

// 9. Always Latch
module driver_09_latch;
    logic clk, en;
    logic [7:0] data_in, data_out;
    
    always_latch begin
        if (en) data_out = data_in;
    end
endmodule

// 10. Mixed Blocking/Nonblocking
module driver_10_mixed;
    logic clk;
    logic [7:0] a, b, c;
    
    always_ff @(posedge clk) begin
        a <= b;
        b <= c;
        c = a + 1;
    end
endmodule

