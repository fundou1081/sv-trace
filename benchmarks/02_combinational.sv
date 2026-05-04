// Test 2: always_comb and ternary
module basic_combinational (
    input  logic [7:0] a,
    input  logic [7:0] b,
    input  logic       sel,
    output logic [7:0] result1,
    output logic [7:0] result2
);
    // 多路选择器
    always_comb begin
        if (sel)
            result1 = a;
        else
            result1 = b;
    end
    
    // 三元表达式
    assign result2 = sel ? a : b;
endmodule
