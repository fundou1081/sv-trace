// ============================================================================
// Package 测试用例
// ============================================================================

// Test 1: 简单包
package simple_pkg;
    logic [7:0] constant1 = 8'hAB;
    logic [3:0] constant2 = 4'h5;
endpackage

// Test 2: 带类型的包
package types_pkg;
    typedef logic [7:0] byte_t;
    typedef logic [15:0] word_t;
    typedef enum {IDLE, RUN, DONE} state_t;
endpackage

// Test 3: 带函数的包
package functions_pkg;
    function logic [7:0] add_one(logic [7:0] x);
        return x + 1;
    endfunction
    
    function logic [7:0] clamp(logic [7:0] x, logic [7:0] min_val, logic [7:0] max_val);
        return (x < min_val) ? min_val : (x > max_val) ? max_val : x;
    endfunction
endpackage
