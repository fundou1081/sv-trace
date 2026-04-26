// ============================================================================
// BitSelect 测试用例 - 位选择分析
// ============================================================================

// Test 1: 简单位选择
module test_bs_simple;
    logic [7:0] data;
    logic bit0;
    
    assign bit0 = data[0];
endmodule

// Test 2: 多位选择
module test_bs_multi;
    logic [15:0] data;
    logic [7:0] byte0;
    
    assign byte0 = data[7:0];
endmodule

// Test 3: 动态位选择
module test_bs_dynamic;
    logic [7:0] data;
    logic [2:0] sel;
    logic bit;
    
    assign bit = data[sel];
endmodule

// Test 4: 动态范围选择
module test_bs_range;
    logic [15:0] data;
    logic [2:0] sel;
    logic [3:0] part;
    
    assign part = data[sel+:4];
endmodule

// Test 5: 反向位选择
module test_bs_reverse;
    logic [7:0] data;
    logic bit7;
    
    assign bit7 = data[7];
endmodule

// Test 6: 条件位选择
module test_bs_cond;
    logic [7:0] data;
    logic sel;
    logic bit;
    
    assign bit = sel ? data[3] : data[4];
endmodule

// Test 7: 拼接位选择
module test_bs_concat;
    logic [3:0] a, b;
    logic [7:0] combined;
    
    assign combined = {a, b};
endmodule

// Test 8: 移位位选择
module test_bs_shift;
    logic [7:0] data;
    logic [2:0] shamt;
    logic bit;
    
    assign bit = data[shamt];
endmodule

// Test 9: 比较位选择
module test_bs_compare;
    logic [7:0] data;
    logic result;
    
    assign result = data[3] & data[5];
endmodule

// Test 10: 选择器位选择
module test_bs_mux;
    logic [7:0] a, b;
    logic sel;
    logic bit;
    
    assign bit = sel ? a[0] : b[0];
endmodule

// Test 11: case位选择
module test_bs_case;
    logic [7:0] data;
    logic [1:0] sel;
    logic bit;
    
    always_comb begin
        case (sel)
            2'b00: bit = data[0];
            2'b01: bit = data[1];
            2'b10: bit = data[2];
            default: bit = data[3];
        endcase
    end
endmodule

// Test 12: 嵌套位选择
module test_bs_nested;
    logic [15:0] data;
    logic [3:0] bits;
    
    assign bits = data[3:0];
endmodule

// Test 13: 多位选择
module test_bs_multi_sel;
    logic [15:0] data;
    logic [7:0] low, mid, high;
    
    assign low = data[7:0];
    assign mid = data[11:4];
    assign high = data[15:8];
endmodule

// Test 14: 条件多位选择
module test_bs_cond_multi;
    logic [15:0] data;
    logic sel;
    logic [7:0] part;
    
    assign part = sel ? data[7:0] : data[15:8];
endmodule

// Test 15: 函数位选择
module test_bs_func;
    logic [7:0] data;
    logic bit;
    
    assign bit = get_bit(data, 3);
    
    function logic get_bit(input [7:0] d, input [2:0] idx);
        begin
            get_bit = d[idx];
        end
    endfunction
endmodule

// Test 16: 归约位选择
module test_bs_reduction;
    logic [7:0] data;
    logic or_all, and_all;
    
    assign or_all = |data;
    assign and_all = &data;
endmodule

// Test 17: 跨模块位选择
module test_bs_cross;
    logic [7:0] parent;
    logic bit;
    
    sub_bs u_sub (.sig(parent), .bit(bit));
endmodule

module sub_bs (
    input  logic [7:0] sig,
    output logic bit
);
    assign bit = sig[2];
endmodule

// Test 18: always块位选择
module test_bs_always;
    logic clk;
    logic [7:0] data, result;
    
    always_ff @(posedge clk)
        result[0] <= data[0];
endmodule

// Test 19: 生成块位选择
module test_bs_gen;
    logic [7:0] data;
    logic [3:0] bits [0:1];
    
    assign bits[0] = data[3:0];
    assign bits[1] = data[7:4];
endmodule

// Test 20: 边沿检测
module test_bs_edge;
    logic clk;
    logic [7:0] data, old_data, edge;
    
    always_ff @(posedge clk) begin
        old_data <= data;
        edge <= data[0] ^ old_data[0];
    end
endmodule
