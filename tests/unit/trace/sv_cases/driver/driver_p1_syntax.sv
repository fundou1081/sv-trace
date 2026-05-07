// ============================================================================
// DriverTracer P1 语法测试
// 测试 for loop, function, task, generate if
// ============================================================================

// 1. For Loop 中的驱动
module p1_01_for_loop;
    logic clk, rst_n;
    logic [7:0] data [0:3];
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < 4; i++) begin
                data[i] <= 8'h0;
            end
        end else begin
            for (int i = 0; i < 4; i++) begin
                data[i] <= data[i] + 1;
            end
        end
    end
endmodule

// 2. Function 中的驱动
module p1_02_function;
    logic clk, rst_n;
    logic [7:0] a, b, result;
    
    function logic [7:0] add(input logic [7:0] x, y);
        return x + y;
    endfunction
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            result <= 8'h0;
        else
            result <= add(a, b);
    end
endmodule

// 3. Task 中的驱动
module p1_03_task;
    logic clk, rst_n;
    logic [7:0] data;
    
    task reset_data(output logic [7:0] d);
        d <= 8'h0;
    endtask
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            reset_data(data);
        else
            data <= data + 1;
    end
endmodule

// 4. Generate If 中的驱动
module p1_04_generate_if;
    parameter USE_RESET = 1;
    logic clk, rst_n;
    logic [7:0] data;
    
    generate
        if (USE_RESET) begin : gen_reset
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    data <= 8'h0;
                else
                    data <= data + 1;
            end
        end else begin : gen_no_reset
            always_ff @(posedge clk) begin
                data <= data + 1;
            end
        end
    endgenerate
endmodule

// 5. Foreach Loop 中的驱动
module p1_05_foreach;
    logic clk, rst_n;
    logic [7:0] data [0:3];
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            foreach (data[i]) begin
                data[i] <= 8'h0;
            end
        end else begin
            foreach (data[i]) begin
                data[i] <= data[i] + 1;
            end
        end
    end
endmodule

// 6. While Loop 中的驱动
module p1_06_while;
    logic clk, rst_n;
    logic [7:0] data;
    int i;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            i = 0;
            while (i < 8) begin
                data[i] <= 1'b0;
                i++;
            end
        end
    end
endmodule
