// ============================================================================
// ClockTreeAnalyzer 测试用例 - 时钟树分析测试
// ============================================================================

// Test 1: 单一时钟
module test_clock_single;
    logic clk;
    logic [7:0] reg_q;
    
    always_ff @(posedge clk)
        reg_q <= 8'h00;
endmodule

// Test 2: 多时钟域
module test_clock_multi;
    logic clk_a, clk_b;
    logic [7:0] reg_a, reg_b;
    
    always_ff @(posedge clk_a)
        reg_a <= 8'h01;
    
    always_ff @(posedge clk_b)
        reg_b <= 8'h02;
endmodule

// Test 3: 门控时钟
module test_clock_gated;
    logic clk, clk_en;
    logic [7:0] reg_q;
    
    // 时钟门控
    logic gated_clk;
    assign gated_clk = clk & clk_en;
    
    always_ff @(posedge gated_clk)
        reg_q <= 8'h00;
endmodule

// Test 4: 时钟分频
module test_clock_divide;
    logic clk, rst_n;
    logic [7:0] reg_q;
    logic clk_div2;
    
    // 2分频
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            clk_div2 <= 1'b0;
        else
            clk_div2 <= ~clk_div2;
    end
    
    always_ff @(posedge clk_div2)
        reg_q <= 8'h01;
endmodule

// Test 5: 异步时钟
module test_clock_async;
    logic clk_a, clk_b;
    logic [7:0] reg_a, reg_sync;
    
    always_ff @(posedge clk_a)
        reg_a <= 8'h01;
    
    // 跨时钟域同步
    always_ff @(posedge clk_b)
        reg_sync <= reg_a;
endmodule

// Test 6: 多个寄存器同一时钟驱动
module test_clock_fanout;
    logic clk;
    logic [7:0] reg0, reg1, reg2, reg3, reg4;
    
    always_ff @(posedge clk) begin
        reg0 <= 8'h00;
        reg1 <= 8'h01;
        reg2 <= 8'h02;
        reg3 <= 8'h03;
        reg4 <= 8'h04;
    end
endmodule

// Test 7: 时钟选择 (MUX)
module test_clock_mux;
    logic clk_a, clk_b, sel;
    logic [7:0] reg_q;
    logic clk_sel;
    
    assign clk_sel = sel ? clk_a : clk_b;
    
    always_ff @(posedge clk_sel)
        reg_q <= 8'h00;
endmodule

// Test 8: 层次化时钟
module test_clock_hierarchy;
    logic clk;
    logic [7:0] reg_top;
    
    child_clk u_child (.clk(clk), .reg_out(reg_top));
endmodule

module child_clk (
    input  logic clk,
    output logic [7:0] reg_out
);
    logic [7:0] reg_mid;
    
    always_ff @(posedge clk) begin
        reg_mid <= 8'h01;
        reg_out <= reg_mid;
    end
endmodule

// Test 9: PLL时钟
module test_clock_pll;
    logic ref_clk, pll_clk;
    logic [7:0] reg_q;
    
    // 简化的PLL
    assign pll_clk = ref_clk;
    
    always_ff @(posedge pll_clk)
        reg_q <= 8'h00;
endmodule

// Test 10: 时钟缓冲器
module test_clock_buffer;
    logic clk_in, clk_buf;
    logic [7:0] reg_q;
    
    // 缓冲器
    buf u_buf (.in(clk_in), .out(clk_buf));
    
    always_ff @(posedge clk_buf)
        reg_q <= 8'h00;
endmodule

module buf (
    input  logic in,
    output logic out
);
    assign out = in;
endmodule

// Test 11: 多级时钟分频
module test_clock_multistage;
    logic clk, clk_div2, clk_div4;
    logic [7:0] reg2, reg4;
    
    always_ff @(posedge clk) begin
        clk_div2 <= ~clk_div2;
        clk_div4 <= ~clk_div4;
    end
    
    always_ff @(posedge clk_div2)
        reg2 <= 8'h01;
    
    always_ff @(posedge clk_div4)
        reg4 <= 8'h02;
endmodule

// Test 12: 时钟使能
module test_clock_enable;
    logic clk, enable;
    logic [7:0] reg_q;
    
    always_ff @(posedge clk) begin
        if (enable)
            reg_q <= reg_q + 1;
    end
endmodule
