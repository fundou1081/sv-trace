// ============================================================================
// Function/Task 测试用例
// ============================================================================

// Test 1: 简单函数
module func_simple;
    function bit [7:0] add_one(input bit [7:0] x);
        return x + 1;
    endfunction
endmodule

// Test 2: 复杂函数
module func_complex;
    function logic [31:0] multiply_add(
        input logic [15:0] a,
        input logic [15:0] b,
        input logic [31:0] c
    );
        multiply_add = (a * b) + c;
    endfunction
endmodule

// Test 3: 任务
module task_simple;
    task reset();
        rst_n = 0;
        #10 rst_n = 1;
    endtask
endmodule

// Test 4: 带超时保护的任务
module task_timeout;
    task wait_for_ack();
        fork
            begin
                @(posedge ack);
            end
            begin
                #1000;
                $display("Timeout waiting for ack");
            end
        join_any
        disable fork;
    endtask
endmodule

// Test 5: 自动函数
module func_automatic;
    function automatic int factorial(input int n);
        if (n <= 1)
            return 1;
        else
            return n * factorial(n - 1);
    endfunction
endmodule
