// ============================================================================
// Condition Coverage Corner Cases - 条件覆盖边界测试
// ============================================================================

module condition_corners_all;
    logic a, b, c, d, e, f;
    logic [3:0] sel;
    logic [7:0] cnt;
    logic [15:0] data;
    logic result;
    
    // Test 1: 位选择条件
    always_comb begin
        if (data[0])      // 位选择
            result = 1;
        else if (data[7])
            result = 2;
        else if (cnt[3])
            result = 3;
        else
            result = 0;
    end
    
    // Test 2: 拼接条件
    always_comb begin
        if ({a, b, c, d} == 4'b1010)  // 拼接
            result = 1;
        else if ({a, b} == 2'b11)
            result = 2;
        else
            result = 0;
    end
    
    // Test 3: 比较符条件
    always_comb begin
        if (cnt > 8'd100)     // 无符号大于
            result = 1;
        else if (cnt < 8'd10) // 无符号小于
            result = 2;
        else if (cnt == 8'd50) // 等于
            result = 3;
        else if (cnt != 8'd0)  // 不等于
            result = 4;
        else if (data[7:4] >= 4'hA)  // 范围比较
            result = 5;
        else
            result = 0;
    end
    
    // Test 4: 恒真/恒假条件
    always_comb begin
        if (1'b1)      // 恒真 - 永远执行
            result = 1;
        else if (1'b0) // 恒假 - 永不执行
            result = 2;
        else
            result = 0;
    end
    
    // Test 5: 多路复用器(Mux)
    always_comb begin
        case (sel)
            4'b0000: result = a ? 1 : 0;
            4'b0001: result = b ? 2 : 0;
            4'b0010: result = c ? 3 : 0;
            4'b0011: result = d ? 4 : 0;
            4'b0100: result = (a && b) ? 5 : 0;
            4'b0101: result = (c || d) ? 6 : 0;
            default: result = 0;
        endcase
    end
    
    // Test 6: casez/wildcard
    always_comb begin
        casez (sel)
            4'b000?: result = 1;  // wildcard
            4'b001?: result = 2;
            4'b01??: result = 3;
            4'b1???: result = 4;
            default: result = 0;
        endcase
    end
    
    // Test 7: 条件中含函数
    logic [7:0] func_result;
    function logic [7:0] calc(input logic [7:0] x);
        return x * 2 + 1;
    endfunction
    
    always_comb begin
        if (calc(cnt) > 8'd100)
            result = 1;
        else
            result = 0;
    end
    
    // Test 8: 复杂组合条件
    always_comb begin
        if ((a && b) || (c && (d || e)) || (f && !a))
            result = 1;
        else if ((a ^ b) && (c | d))
            result = 2;
        else if (~(a && b) || (c && !d))
            result = 3;
        else
            result = 0;
    end
    
    // Test 9: 嵌套三元表达式
    always_comb begin
        result = a ? (b ? 1 : 2) : (c ? 3 : (d ? 4 : 0));
    end
    
    // Test 10: 条件中含延迟
    logic a_d1, b_d1;
    always_ff @(posedge clk) begin
        a_d1 <= a;
        b_d1 <= b;
    end
    
    always_comb begin
        if (a && !a_d1)    // 上升沿检测
            result = 1;
        else if (!b && b_d1)  // 下降沿检测
            result = 2;
        else
            result = 0;
    end
    
    logic clk;
endmodule


// Test 11: 多层嵌套if
module condition_deep_nesting;
    logic a, b, c, d, e, f;
    logic result;
    logic [2:0] level;
    
    always_comb begin
        if (a) begin
            if (b) begin
                if (c) begin
                    if (d) begin
                        if (e) begin
                            if (f)
                                result = 6;  // 6层嵌套
                            else
                                result = 5;
                        end else
                            result = 4;
                    end else
                        result = 3;
                end else
                    result = 2;
            end else
                result = 1;
        end else
            result = 0;
    end
endmodule


// Test 12: 条件中的状态机引用
module condition_with_fsm;
    typedef enum logic [1:0] {
        IDLE, RUN, WAIT, DONE
    } state_t;
    
    state_t state;
    logic enable, start, stop;
    logic result;
    
    always_comb begin
        if (state == IDLE && start && enable)
            result = 1;
        else if (state == RUN && !stop)
            result = 2;
        else if (state == WAIT && enable)
            result = 3;
        else if (state == DONE)
            result = 4;
        else
            result = 0;
    end
    
    logic clk, rst_n;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= WAIT;
    end
endmodule


// Test 13: 移位操作条件
module condition_shift_ops;
    logic [7:0] data;
    logic [2:0] shift;
    logic result;
    
    always_comb begin
        if (data << shift > 8'h80)  // 左移比较
            result = 1;
        else if (data >> shift < 8'h10)  // 右移比较
            result = 2;
        else if ({data, 1'b0} == 9'b0)  // 拼接移位
            result = 3;
        else
            result = 0;
    end
endmodule


// Test 14: 重复条件
module condition_repeated;
    logic a, b, c;
    logic result;
    
    always_comb begin
        // a出现多次
        if (a && b)
            result = 1;
        else if (!a && c)
            result = 2;
        else if (a || (!b && c)
            result = 3;
        else if (!a && !b && !c)
            result = 4;
        else
            result = 0;
    end
endmodule
