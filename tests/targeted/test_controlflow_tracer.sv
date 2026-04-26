// ============================================================================
// ControlFlowTracer 测试用例 - 验证控制流分析功能
// ============================================================================

// Test 1: 简单if-else控制流
module test_cf_if_else;
    logic [7:0] a, b, result;
    logic enable;
    
    always_comb begin
        if (enable)
            result = a;
        else
            result = b;
    end
endmodule

// Test 2: 嵌套if控制流
module test_cf_nested_if;
    logic a, b, c;
    logic [7:0] result;
    
    always_comb begin
        if (a) begin
            if (b)
                result = 8'h01;
            else
                result = 8'h02;
        end else begin
            if (c)
                result = 8'h03;
            else
                result = 8'h04;
        end
    end
endmodule

// Test 3: case控制流
module test_cf_case;
    logic [1:0] sel;
    logic [7:0] result;
    
    always_comb begin
        case (sel)
            2'b00: result = 8'hAA;
            2'b01: result = 8'h55;
            2'b10: result = 8'hF0;
            default: result = 8'h00;
        endcase
    end
endmodule

// Test 4: casez控制流 (z为任意值)
module test_cf_casez;
    logic [7:0] pattern;
    logic [7:0] result;
    
    always_comb begin
        casez (pattern)
            8'b1???_????: result = 8'h01;
            8'b0???_????: result = 8'h02;
            default: result = 8'h00;
        endcasez
    end
endmodule

// Test 5: casex控制流 (x为任意值，不比较)
module test_cf_casex;
    logic [7:0] pattern;
    logic [7:0] result;
    
    always_comb begin
        casex (pattern)
            8'b1xx_xxxx: result = 8'h01;
            8'b0xx_xxxx: result = 8'h02;
            default: result = 8'h00;
        endcasex
    end
endmodule

// Test 6: if-elsif-else链
module test_cf_elsif;
    logic [1:0] sel;
    logic [7:0] result;
    
    always_comb begin
        if (sel == 2'b00)
            result = 8'h01;
        else if (sel == 2'b01)
            result = 8'h02;
        else if (sel == 2'b10)
            result = 8'h03;
        else
            result = 8'h00;
    end
endmodule

// Test 7: always_ff时序控制流
module test_cf_always_ff;
    logic clk;
    logic [7:0] counter;
    logic rst_n;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            counter <= 8'h00;
        else
            counter <= counter + 1;
    end
endmodule

// Test 8: always_comb组合控制流
module test_cf_always_comb;
    logic [7:0] a, b;
    logic [7:0] result;
    
    always_comb begin
        result = a & b;
    end
endmodule

// Test 9: always_latch锁存控制流
module test_cf_always_latch;
    logic enable;
    logic [7:0] data_in, latch_out;
    
    always_latch begin
        if (enable)
            latch_out = data_in;
    end
endmodule

// Test 10: 三元表达式控制流
module test_cf_ternary;
    logic [7:0] a, b;
    logic sel;
    logic [7:0] result;
    
    assign result = sel ? a : b;
endmodule

// Test 11: 优先编码器控制流
module test_cf_priority;
    logic [3:0] req;
    logic [1:0] grant;
    
    always_comb begin
        if (req[3])
            grant = 2'd3;
        else if (req[2])
            grant = 2'd2;
        else if (req[1])
            grant = 2'd1;
        else if (req[0])
            grant = 2'd0;
        else
            grant = 2'd0;
    end
endmodule

// Test 12: 条件赋值控制流
module test_cf_cond_assign;
    logic [7:0] a, b;
    logic [7:0] result;
    
    assign result = (a > b) ? a : b;
endmodule

// Test 13: for循环控制流
module test_cf_for;
    logic [7:0] i;
    logic [7:0] result;
    
    always_comb begin
        result = 0;
        for (i = 0; i < 4; i++) begin
            result = result + i;
        end
    end
endmodule

// Test 14: while循环控制流 (综合可能不支持)
module test_cf_while;
    logic clk;
    logic [7:0] counter;
    
    always_ff @(posedge clk) begin
        if (counter < 8'h10)
            counter <= counter + 1;
    end
endmodule

// Test 15: do-while循环控制流
module test_cf_do_while;
    logic clk;
    logic [7:0] counter;
    
    always_ff @(posedge clk)
        counter <= counter + 1;
endmodule

// Test 16: 生成块if控制流
module test_cf_gen_if;
    parameter WIDTH = 8;
    logic clk;
    logic [WIDTH-1:0] out;
    
    generate
        if (WIDTH > 4) begin : gen_wide
            always_ff @(posedge clk)
                out <= {WIDTH{1'b0}};
        end else begin : gen_narrow
            always_ff @(posedge clk)
                out <= {WIDTH{1'b1}};
        end
    endgenerate
endmodule

// Test 17: 生成块case控制流
module test_cf_gen_case;
    parameter N = 3;
    logic [1:0] sel;
    logic [7:0] out;
    
    generate
        case (N)
            1: assign out = 8'h01;
            2: assign out = 8'h02;
            3: assign out = 8'h03;
            default: assign out = 8'h00;
        endcase
    endgenerate
endmodule

// Test 18: function控制流
module test_cf_function;
    logic [7:0] a, b, result;
    
    always_comb begin
        result = max(a, b);
    end
    
    function [7:0] max(input [7:0] x, y);
        begin
            max = (x > y) ? x : y;
        end
    endfunction
endmodule
