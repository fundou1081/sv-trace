// ============================================================================
// DriverTracer P3 语法测试
// 测试 assert, covergroup, sequence, property
// ============================================================================

// 1. Assert Statement
module p3_01_assert;
    logic clk, rst_n;
    logic [7:0] data;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data <= 8'h0;
        else
            data <= data + 1;
    end
    
    // Assert property check
    assert property (@(posedge clk) data >= 0);
endmodule

// 2. Assert with else
module p3_02_assert_else;
    logic clk, rst_n;
    logic [7:0] data;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data <= 8'h0;
        else
            data <= data + 1;
    end
    
    assert property (@(posedge clk) data >= 0) else $error("Error");
endmodule

// 3. Covergroup
module p3_03_covergroup;
    logic clk, rst_n;
    logic [7:0] data;
    
    covergroup cov @(posedge clk);
        coverpoint data {
            bins low = {0..127};
            bins high = {128..255};
        }
    endgroup
    
    cov cg;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data <= 8'h0;
        else
            data <= data + 1;
    end
    
    initial cg = new();
endmodule

// 4. Immediate Assert
module p3_04_immediate_assert;
    logic [7:0] a, b;
    
    always_comb begin
        assert (a != b) else $error("Mismatch");
    end
endmodule

// 5. Sequence
module p3_05_sequence;
    logic clk, a, b;
    
    sequence req_ack;
        @(posedge clk) a ##1 b;
    endsequence
    
    property p;
        req_ack;
    endproperty
    
    assert property (p);
endmodule

// 6. Property with clocking
module p3_06_property;
    logic clk, rst_n;
    logic [7:0] data;
    
    property stable;
        @(posedge clk) not (data != $past(data));
    endproperty
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data <= 8'h0;
        else
            data <= data + 1;
    end
    
    assert property (stable);
endmodule
