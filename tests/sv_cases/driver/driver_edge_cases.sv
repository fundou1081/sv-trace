// ============================================================================
// DriverTracer 边界语法测试
// 测试各种边界语法场景
// ============================================================================

// 1. Generate For 中的驱动
module edge_01_generate_for;
    logic clk, rst_n;
    logic [7:0] data [0:3];
    genvar i;
    generate
        for (i = 0; i < 4; i = i + 1) begin : gen_block
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    data[i] <= 8'h0;
                else
                    data[i] <= data[i] + 1;
            end
        end
    endgenerate
endmodule

// 2. 多个 always_ff 块
module edge_02_multi_always_ff;
    logic clk, rst_n;
    logic [7:0] a, b, c;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            a <= 8'h0;
        else
            a <= a + 1;
    end
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            b <= 8'h0;
        else
            b <= a + c;
    end
endmodule

// 3. 嵌套 if 语句
module edge_03_nested_if;
    logic clk, rst_n, en, mode;
    logic [7:0] data;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data <= 8'h0;
        else if (en) begin
            if (mode)
                data <= data + 1;
            else
                data <= data - 1;
        end
    end
endmodule

// 4. Case 语句
module edge_04_case;
    logic clk, rst_n;
    logic [1:0] sel;
    logic [7:0] data;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data <= 8'h0;
        else begin
            case (sel)
                2'b00: data <= data + 1;
                2'b01: data <= data - 1;
                2'b10: data <= data << 1;
                default: data <= data;
            endcase
        end
    end
endmodule

// 5. 连续赋值 (assign)
module edge_05_continuous_assign;
    logic [7:0] a, b, c;
    
    assign c = a + b;
    assign a = 8'h01;
endmodule

// 6. AlwaysComb
module edge_06_always_comb;
    logic [7:0] a, b, c;
    logic sel;
    
    always_comb begin
        if (sel)
            c = a;
        else
            c = b;
    end
endmodule

// 7. 接口时钟
module edge_07_negedge_clk;
    logic clk, rst;
    logic [7:0] data;
    
    always_ff @(negedge clk) begin
        if (rst)
            data <= 8'h0;
        else
            data <= data + 1;
    end
endmodule

// 8. 条件赋值
module edge_08_conditional;
    logic clk, rst_n, en;
    logic [7:0] data;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data <= 8'h0;
        else
            data <= en ? data + 1 : data;
    end
endmodule
