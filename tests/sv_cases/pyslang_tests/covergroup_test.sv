// ============================================================================
// Covergroup 测试用例
// ============================================================================

// Test 1: 简单覆盖组
module cover_simple;
    covergroup cg_simple;
        coverpoint data;
    endgroup
endmodule

// Test 2: 带bins的覆盖点
module cover_bins;
    logic [7:0] data;
    
    covergroup cg_bins;
        cp_data: coverpoint data {
            bins zero = {0};
            bins low = {[1:127]};
            bins high = {[128:254]};
            bins max = {255};
        }
    endgroup
endmodule

// Test 3: 交叉覆盖
module cover_cross;
    logic [1:0] mode;
    logic [1:0] state;
    
    covergroup cg_cross;
        cp_mode: coverpoint mode;
        cp_state: coverpoint state;
        cross cp_mode, cp_state;
    endgroup
endmodule

// Test 4: 带有条件的覆盖点
module cover_conditional;
    logic [7:0] data;
    logic valid;
    
    covergroup cg_cond;
        cp_data: coverpoint data iff (valid) {
            bins valid_data = {[0:127]};
        }
    endgroup
endmodule
