// ============================================================================
// Condition Coverage Targeted Test Cases - 条件覆盖专项测试
// ============================================================================

module condition_test_basic;
    logic a, b, c, d;
    logic result;
    
    // Test 1: 简单条件
    always_comb begin
        if (a && b)      // 2个条件的and
            result = 1;
        else if (c || d) // 2个条件的or
            result = 2;
        else
            result = 0;
    end
    
    // Test 2: 嵌套条件
    always_comb begin
        if (a) begin
            if (b) begin
                if (c)
                    result = 1;
                else
                    result = 2;
            end else begin
                result = 3;
            end
        end else begin
            result = 0;
        end
    end
    
    // Test 3: 中间变量展开
    logic flag1, flag2, flag3;
    logic intermediate1, intermediate2;
    
    always_comb begin
        // 中间变量
        intermediate1 = a && b;
        intermediate2 = c || d;
        flag1 = intermediate1 || intermediate2;
        flag2 = a ^ b ^ c;
        flag3 = (a && !b) || (!a && b);
        
        if (flag1 && flag2)
            result = 1;
        else if (flag3)
            result = 2;
        else
            result = 0;
    end
    
    // Test 4: 复杂逻辑表达式
    always_comb begin
        if ((a && b) || (c && d) || (a && c))
            result = 1;
        else if ((a || b) && (c || d))
            result = 2;
        else if (a ^ b ^ c ^ d)
            result = 3;
        else
            result = 0;
    end
    
    // Test 5: 多级中间变量
    logic level1, level2, level3, level4;
    logic final_flag;
    
    always_comb begin
        level1 = a && b;
        level2 = c && d;
        level3 = level1 || level2;  // 中间变量
        level4 = level1 && level2;
        final_flag = level3 || level4;
        
        if (final_flag)
            result = 1;
        else
            result = 0;
    end
endmodule


// Test 6: case条件
module condition_test_case;
    logic [1:0] sel;
    logic a, b, c, d;
    logic result;
    
    always_comb begin
        case (sel)
            2'b00: result = a ? 1 : 0;
            2'b01: result = b ? 2 : 0;
            2'b10: result = c ? 3 : 0;
            2'b11: result = d ? 4 : 0;
        endcase
    end
endmodule


// Test 7: 三元表达式条件
module condition_test_ternary;
    logic a, b, c;
    logic [1:0] result;
    
    always_comb begin
        result = a ? (b ? 2'b01 : 2'b00) : (c ? 2'b11 : 2'b10);
    end
endmodule
