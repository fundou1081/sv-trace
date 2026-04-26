// ============================================================================
// ControlFlowTracer 底层功能测试
// 测试控制流分析的各种场景
// ============================================================================

// Test 1: 简单if-else
module controlflow_if_else;
    logic clk;
    logic [7:0] a, b, result;
    
    always_comb begin
        if (a > b)
            result = a;
        else
            result = b;
    end
endmodule


// Test 2: 嵌套if
module controlflow_nested_if;
    logic clk;
    logic [7:0] a, b, c, result;
    
    always_comb begin
        if (a > 0) begin
            if (b > 0)
                result = a + b;
            else
                result = a - b;
        end else begin
            result = 0;
        end
    end
endmodule


// Test 3: if-else if-else链
module controlflow_if_elseif;
    logic [1:0] sel;
    logic [7:0] a, b, c, d, result;
    
    always_comb begin
        if (sel == 2'b00)
            result = a;
        else if (sel == 2'b01)
            result = b;
        else if (sel == 2'b10)
            result = c;
        else
            result = d;
    end
endmodule


// Test 4: case语句
module controlflow_case;
    logic [2:0] state;
    logic [7:0] result;
    
    always_comb begin
        case (state)
            3'd0: result = 8'h00;
            3'd1: result = 8'h01;
            3'd2: result = 8'h02;
            3'd3: result = 8'h03;
            3'd4: result = 8'h04;
            3'd5: result = 8'h05;
            3'd6: result = 8'h06;
            default: result = 8'hFF;
        endcase
    end
endmodule


// Test 5: casez (don't care)
module controlflow_casez;
    logic [7:0] data;
    logic [7:0] result;
    
    always_comb begin
        casez (data)
            8'b1???????: result = 8'h80;  // 最高位为1
            8'b01??????: result = 8'h40;  // 最高两位为01
            8'b001?????: result = 8'h20;  // 最高三位为001
            default: result = 8'h00;
        endcase
    end
endmodule


// Test 6: 嵌套always块
module controlflow_nested_always;
    logic clk;
    logic [7:0] a, b, c, r1, r2;
    
    always_ff @(posedge clk) begin
        if (a > 0) begin
            r1 <= a + 1;
            if (b > 0) begin
                r2 <= b + 1;
            end
        end
    end
    
    always_comb begin
        c = r1 + r2;
    end
endmodule


// Test 7: 组合逻辑always块
module controlflow_always_comb;
    logic [7:0] a, b, c, result;
    
    always_comb begin
        result = 0;
        if (a > b)
            result = a - b;
        if (c > result)
            result = c;
    end
endmodule


// Test 8: 锁存器always块
module controlflow_always_latch;
    logic clk;
    logic [7:0] data;
    logic enable;
    logic [7:0] latch;
    
    always_latch begin
        if (enable)
            latch = data;
    end
endmodule


// Test 9: 三元表达式
module controlflow_ternary;
    logic [7:0] a, b, result;
    
    assign result = (a > b) ? a : b;
endmodule


// Test 10: 多路复用器
module controlflow_mux4;
    logic [1:0] sel;
    logic [7:0] in0, in1, in2, in3;
    logic [7:0] out;
    
    always_comb begin
        out = in0;
        if (sel == 2'b01) out = in1;
        if (sel == 2'b10) out = in2;
        if (sel == 2'b11) out = in3;
    end
endmodule


// Test 11: 优先编码器
module controlflow_priority;
    logic [7:0] req;
    logic [2:0] grant;
    
    always_comb begin
        grant = 0;
        if (req[7]) grant = 3'd7;
        else if (req[6]) grant = 3'd6;
        else if (req[5]) grant = 3'd5;
        else if (req[4]) grant = 3'd4;
        else if (req[3]) grant = 3'd3;
        else if (req[2]) grant = 3'd2;
        else if (req[1]) grant = 3'd1;
        else if (req[0]) grant = 3'd0;
    end
endmodule


// Test 12: 状态机控制流
module controlflow_fsm_control;
    typedef enum logic [1:0] {
        IDLE, RUN, WAIT, DONE
    } state_t;
    
    state_t state, next_state;
    logic start, stop, timeout;
    logic [7:0] counter;
    
    always_comb begin
        next_state = state;
        case (state)
            IDLE: if (start) next_state = RUN;
            RUN: if (stop) next_state = DONE;
                  else if (timeout) next_state = WAIT;
            WAIT: if (!timeout) next_state = RUN;
            DONE: next_state = IDLE;
        endcase
    end
endmodule
