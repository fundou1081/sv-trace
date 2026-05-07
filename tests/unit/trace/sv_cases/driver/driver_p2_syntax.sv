// ============================================================================
// DriverTracer P2 语法测试
// 测试 always @, while, class, interface
// ============================================================================

// 1. Always @ (旧语法)
module p2_01_always_at;
    logic clk, rst_n;
    logic [7:0] data;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data <= 8'h0;
        else
            data <= data + 1;
    end
endmodule

// 2. Always @* (组合逻辑)
module p2_02_always_star;
    logic [7:0] a, b, c;
    
    always @* begin
        c = a + b;
    end
endmodule

// 3. Class 中的驱动
module p2_03_class;
    logic clk, rst_n;
    logic [7:0] data;
    
    class Driver;
        randc logic [7:0] rand_data;
        
        function void drive(output logic [7:0] d);
            d <= rand_data;
        endfunction
    endclass
    
    Driver drv;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            drv = new();
            data <= 8'h0;
        end else begin
            drv.drive(data);
        end
    end
endmodule

// 4. Interface 中的驱动
interface bus_if;
    logic [7:0] data;
    logic valid;
    
    modport master(output data, output valid);
    modport slave(input data, input valid);
endinterface

module p2_04_interface;
    logic clk, rst_n;
    bus_if.master bus;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bus.data <= 8'h0;
            bus.valid <= 1'b0;
        end else begin
            bus.data <= bus.data + 1;
            bus.valid <= 1'b1;
        end
    end
endmodule

// 5. Do While Loop
module p2_05_do_while;
    logic clk, rst_n;
    logic [7:0] data;
    int i;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            i = 0;
            do begin
                data[i] <= 1'b0;
                i++;
            end while (i < 8);
        end
    end
endmodule

// 6. Repeat Loop
module p2_06_repeat;
    logic clk, rst_n;
    logic [7:0] data;
    int i;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            i = 0;
            repeat (8) begin
                data[i] <= 1'b0;
                i++;
            end
        end
    end
endmodule
