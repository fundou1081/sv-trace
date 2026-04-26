// ============================================================================
// PowerEstimation 测试用例 - 功耗估计
// ============================================================================

// Test 1: 时序功耗
module test_power_seq;
    logic clk;
    logic [7:0] reg_q;
    
    always_ff @(posedge clk)
        reg_q <= 8'h00;
endmodule

// Test 2: 组合逻辑功耗
module test_power_comb;
    logic [7:0] a, b, result;
    
    assign result = a & b;
endmodule

// Test 3: 乘法器功耗
module test_power_mult;
    logic clk;
    logic [7:0] a, b, prod;
    
    always_ff @(posedge clk)
        prod <= a * b;
endmodule

// Test 4: 加法器功耗
module test_power_add;
    logic [7:0] a, b, sum;
    
    assign sum = a + b;
endmodule

// Test 5: 比较器功耗
module test_power_cmp;
    logic [7:0] a, b;
    logic gt;
    
    assign gt = (a > b);
endmodule

// Test 6: 选择器功耗
module test_power_mux;
    logic [7:0] a, b, sel, out;
    
    assign out = sel ? a : b;
endmodule

// Test 7: 多路选择功耗
module test_power_mux4;
    logic [7:0] in0, in1, in2, in3;
    logic [1:0] sel;
    logic [7:0] out;
    
    always_comb begin
        case (sel)
            2'b00: out = in0;
            2'b01: out = in1;
            2'b10: out = in2;
            default: out = in3;
        endcase
    end
endmodule

// Test 8: 移位功耗
module test_power_shift;
    logic [7:0] data;
    logic [2:0] shamt;
    logic [7:0] shifted;
    
    assign shifted = data << shamt;
endmodule

// Test 9: 归约功耗
module test_power_reduction;
    logic [7:0] data;
    logic parity;
    
    assign parity = ^data;
endmodule

// Test 10: 时钟门控功耗
module test_power_gated;
    logic clk, clk_en;
    logic [7:0] reg_q;
    logic gated_clk;
    
    assign gated_clk = clk & clk_en;
    
    always_ff @(posedge gated_clk)
        reg_q <= 8'h00;
endmodule

// Test 11: 多寄存器功耗
module test_power_regs;
    logic clk;
    logic [7:0] r1, r2, r3, r4, r5;
    
    always_ff @(posedge clk) begin
        r1 <= 8'h00;
        r2 <= r1;
        r3 <= r2;
        r4 <= r3;
        r5 <= r4;
    end
endmodule

// Test 12: RAM访问功耗
module test_power_ram;
    logic clk;
    logic [7:0] addr, wdata, rdata;
    logic we;
    logic [7:0] mem [0:255];
    
    always_ff @(posedge clk) begin
        if (we)
            mem[addr] <= wdata;
        else
            rdata <= mem[addr];
    end
endmodule

// Test 13: 状态机功耗
module test_power_fsm;
    logic clk, rst_n;
    logic [1:0] state;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= 2'b00;
        else
            state <= state + 1;
    end
endmodule

// Test 14: 多周期功耗
module test_power_multi;
    logic clk;
    logic [7:0] r1, r2, r3;
    
    always_ff @(posedge clk) begin
        r1 <= 8'h00;
        r2 <= r1 + 1;
        r3 <= r2 + 1;
    end
endmodule

// Test 15: 异步功耗
module test_power_async;
    logic clk_a, clk_b;
    logic [7:0] reg_a, reg_b;
    
    always_ff @(posedge clk_a)
        reg_a <= 8'h01;
    
    always_ff @(posedge clk_b)
        reg_b <= reg_a;
endmodule

// Test 16: Pipeline功耗
module test_power_pipe;
    logic clk;
    logic [7:0] s1, s2, s3;
    
    always_ff @(posedge clk) begin
        s1 <= 8'h00;
        s2 <= s1;
        s3 <= s2;
    end
endmodule

// Test 17: FIFO功耗
module test_power_fifo;
    logic clk;
    logic [7:0] din, dout;
    logic wr_en, rd_en;
    logic full, empty;
    
    always_ff @(posedge clk) begin
        if (wr_en && !full)
            dout <= din;
    end
endmodule

// Test 18: 时钟分频功耗
module test_power_div;
    logic clk, div_clk;
    logic [7:0] reg_q;
    
    always_ff @(posedge div_clk)
        reg_q <= 8'h00;
endmodule

// Test 19: 使能功耗
module test_power_enable;
    logic clk, enable;
    logic [7:0] reg_q;
    
    always_ff @(posedge clk) begin
        if (enable)
            reg_q <= reg_q + 1;
    end
endmodule

// Test 20: 多时钟功耗
module test_power_multi_clk;
    logic clk1, clk2;
    logic [7:0] r1, r2;
    
    always_ff @(posedge clk1)
        r1 <= 8'h00;
    
    always_ff @(posedge clk2)
        r2 <= 8'h00;
endmodule
