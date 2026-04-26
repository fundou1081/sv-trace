// ============================================================================
// ConditionCoverageAnalyzer 测试用例 - 条件覆盖率测试
// ============================================================================

// Test 1: 简单if条件
module test_cond_simple_if;
    logic a;
    logic [7:0] result;
    
    always_comb begin
        if (a)
            result = 8'h01;
    end
endmodule

// Test 2: if-else条件
module test_cond_if_else;
    logic a;
    logic [7:0] result;
    
    always_comb begin
        if (a)
            result = 8'h01;
        else
            result = 8'h00;
    end
endmodule

// Test 3: 多重if-else条件
module test_cond_multi_if;
    logic [1:0] sel;
    logic [7:0] result;
    
    always_comb begin
        if (sel == 2'b00)
            result = 8'h00;
        else if (sel == 2'b01)
            result = 8'h01;
        else if (sel == 2'b10)
            result = 8'h02;
        else
            result = 8'h03;
    end
endmodule

// Test 4: case条件
module test_cond_case;
    logic [1:0] sel;
    logic [7:0] result;
    
    always_comb begin
        case (sel)
            2'b00: result = 8'h00;
            2'b01: result = 8'h01;
            2'b10: result = 8'h02;
            default: result = 8'h03;
        endcase
    end
endmodule

// Test 5: casez条件
module test_cond_casez;
    logic [7:0] pattern;
    logic result;
    
    always_comb begin
        casez (pattern)
            8'b1???????: result = 1'b1;
            8'b0???????: result = 1'b0;
            default: result = 1'b0;
        endcasez
    end
endmodule

// Test 6: 三元条件
module test_cond_ternary;
    logic sel;
    logic [7:0] a, b, result;
    
    assign result = sel ? a : b;
endmodule

// Test 7: 位选择条件
module test_cond_bitselect;
    logic [7:0] data;
    logic result;
    
    always_comb begin
        if (data[0])
            result = 1'b1;
        else
            result = 1'b0;
    end
endmodule

// Test 8: 比较条件
module test_cond_comparison;
    logic [7:0] a, b;
    logic gt, lt, eq, neq;
    
    assign gt = (a > b);
    assign lt = (a < b);
    assign eq = (a == b);
    assign neq = (a != b);
endmodule

// Test 9: 范围条件
module test_cond_range;
    logic [7:0] value;
    logic in_range;
    
    assign in_range = (value >= 8'h10) && (value <= 8'h20);
endmodule

// Test 10: 组合条件
module test_cond_and;
    logic a, b, c;
    logic result;
    
    assign result = (a && b) || c;
endmodule

// Test 11: 嵌套条件
module test_cond_nested;
    logic a, b;
    logic [7:0] result;
    
    always_comb begin
        if (a) begin
            if (b)
                result = 8'h01;
            else
                result = 8'h02;
        end else begin
            result = 8'h00;
        end
    end
endmodule

// Test 12: 别名条件
module test_cond_alias;
    logic a, b;
    wire c = a;
    logic result;
    
    assign result = c && b;
endmodule
