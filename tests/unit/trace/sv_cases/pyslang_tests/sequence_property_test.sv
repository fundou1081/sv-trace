// ============================================================================
// Sequence/Property/Assert 测试用例
// ============================================================================

// Test 1: 简单序列
module seq_simple;
    sequence simple_seq;
        data ##1 valid;
    endsequence
endmodule

// Test 2: 复杂序列
module seq_complex;
    sequence req_ack_seq;
        req ##[1:3] ack;
    endsequence
endmodule

// Test 3: 属性
module prop_test;
    property data_valid_prop;
        @(posedge clk) disable iff (!rst_n)
        data |-> valid;
    endproperty
endmodule

// Test 4: Assert Statement
module assert_stmt;
    assert property (@posedge clk) rst |-> !err)
    else $error("Reset failed");
endmodule

// Test 5: Assume Statement  
module assume_stmt;
    assume property (@posedge clk) req |-> ##[1:3] ack);
endmodule

// Test 6: Cover Statement
module cover_stmt;
    cover property (@posedge clk) data |-> resp);
endmodule
