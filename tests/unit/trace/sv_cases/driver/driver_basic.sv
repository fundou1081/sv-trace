// ============================================================================
// DriverTracer 测试用例 - 基础驱动
// ============================================================================

module driver_basic;
    // 测试 assign 驱动
    wire [7:0] a, b, c;
    assign a = 8'hFF;
    assign b = a + 1;
    assign c = b & 8'h0F;
endmodule

module driver_always_ff;
    logic clk;
    logic [7:0] data;
    logic [7:0] out;
    
    always_ff @(posedge clk) begin
        out <= data;
    end
endmodule

module driver_always_comb;
    logic [7:0] a, b, c;
    
    always_comb begin
        c = a + b;
    end
endmodule

module driver_if_else;
    logic clk;
    logic [7:0] in_data;
    logic [7:0] out_data;
    logic enable;
    
    always_ff @(posedge clk) begin
        if (enable)
            out_data <= in_data;
        else
            out_data <= 8'h00;
    end
endmodule

module driver_case;
    logic clk;
    logic [1:0] sel;
    logic [7:0] out;
    
    always_ff @(posedge clk) begin
        case (sel)
            2'b00: out <= 8'h00;
            2'b01: out <= 8'hFF;
            2'b10: out <= 8'hAA;
            default: out <= 8'h00;
        endcase
    end
endmodule
