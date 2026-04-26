// ============================================================================
// AreaEstimation 测试用例 - 面积估计
// ============================================================================

// Test 1: 寄存器面积
module test_area_reg;
    logic clk;
    logic [7:0] reg_q;
    
    always_ff @(posedge clk)
        reg_q <= 8'h00;
endmodule

// Test 2: 多寄存器面积
module test_area_regs;
    logic clk;
    logic [7:0] r1, r2, r3, r4;
    
    always_ff @(posedge clk) begin
        r1 <= 8'h00;
        r2 <= r1;
        r3 <= r2;
        r4 <= r3;
    end
endmodule

// Test 3: 加法器面积
module test_area_add;
    logic [7:0] a, b, sum;
    
    assign sum = a + b;
endmodule

// Test 4: 乘法器面积
module test_area_mult;
    logic [7:0] a, b, prod;
    
    assign prod = a * b;
endmodule

// Test 5: 比较器面积
module test_area_cmp;
    logic [7:0] a, b;
    logic eq, gt, lt;
    
    assign eq = (a == b);
    assign gt = (a > b);
    assign lt = (a < b);
endmodule

// Test 6: 选择器面积
module test_area_mux;
    logic [7:0] a, b, sel, out;
    
    assign out = sel ? a : b;
endmodule

// Test 7: 移位器面积
module test_area_shift;
    logic [7:0] data;
    logic [2:0] shamt;
    logic [7:0] result;
    
    assign result = data << shamt;
endmodule

// Test 8: ROM面积
module test_area_rom;
    logic [3:0] addr;
    logic [7:0] data;
    
    always_comb begin
        case (addr)
            4'h0: data = 8'h00;
            4'h1: data = 8'h01;
            4'h2: data = 8'h02;
            default: data = 8'hFF;
        endcase
    end
endmodule

// Test 9: RAM面积
module test_area_ram;
    logic clk;
    logic [7:0] addr, wdata, rdata;
    logic we;
    logic [7:0] mem [0:255];
    
    always_ff @(posedge clk) begin
        if (we)
            mem[addr] <= wdata;
    end
    
    assign rdata = mem[addr];
endmodule

// Test 10: 条件逻辑面积
module test_area_cond;
    logic en;
    logic [7:0] data, result;
    
    always_comb begin
        if (en)
            result = data + 1;
        else
            result = data;
    end
endmodule

// Test 11: 状态机面积
module test_area_fsm;
    logic clk, rst_n;
    logic [1:0] state;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= 2'b00;
        else
            state <= state + 1;
    end
endmodule

// Test 12: 流水线面积
module test_area_pipe;
    logic clk;
    logic [7:0] s1, s2, s3;
    
    always_ff @(posedge clk) begin
        s1 <= 8'h00;
        s2 <= s1;
        s3 <= s2;
    end
endmodule

// Test 13: 多端口面积
module test_area_multiport;
    logic clk;
    logic [7:0] r1, r2, r3;
    
    always_ff @(posedge clk) begin
        r1 <= 8'h00;
        r2 <= 8'h00;
        r3 <= 8'h00;
    end
endmodule

// Test 14: 复用过面积
module test_area_share;
    logic clk, sel;
    logic [7:0] a, b, r;
    
    always_ff @(posedge clk) begin
        if (sel)
            r <= a + 1;
        else
            r <= b + 1;
    end
endmodule

// Test 15: 层次化面积
module test_area_hier;
    logic clk;
    logic [7:0] top;
    
    area_child u_child (.clk(clk), .out(top));
endmodule

module area_child (
    input  logic clk,
    output logic [7:0] out
);
    logic [7:0] reg_sig;
    
    always_ff @(posedge clk)
        reg_sig <= 8'h00;
    
    assign out = reg_sig;
endmodule

// Test 16: 参数化面积
module test_area_param #(
    parameter WIDTH = 8
) (
    input  logic clk,
    input  logic [WIDTH-1:0] data,
    output logic [WIDTH-1:0] out
);
    always_ff @(posedge clk)
        out <= data + 1;
endmodule

// Test 17: 函数面积
module test_area_func;
    logic [7:0] a, b, result;
    
    always_comb begin
        result = my_func(a, b);
    end
    
    function [7:0] my_func(input [7:0] x, y);
        begin
            my_func = x + y;
        end
    endfunction
endmodule

// Test 18: 组合逻辑面积
module test_area_comb;
    logic [7:0] a, b, c, result;
    
    assign result = (a + b) * c;
endmodule

// Test 19: 时序逻辑面积
module test_area_seq;
    logic clk;
    logic [7:0] counter;
    
    always_ff @(posedge clk)
        counter <= counter + 1;
endmodule

// Test 20: 复杂模块面积
module test_area_complex;
    logic clk;
    logic [7:0] a, b, c, r1, r2, r3;
    
    always_ff @(posedge clk) begin
        r1 <= a + b;
        r2 <= r1 + c;
        r3 <= r2 + 1;
    end
endmodule
