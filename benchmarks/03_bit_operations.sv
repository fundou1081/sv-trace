// Test 3: Bit select and concatenation
module bit_operations (
    input  logic [15:0] data_in,
    output logic [7:0]  high_byte,
    output logic [7:0]  low_byte,
    output logic [15:0] byte_swap,
    output logic [31:0] concat_result
);
    // 位选择
    assign high_byte = data_in[15:8];
    assign low_byte = data_in[7:0];
    
    // 字节交换
    assign byte_swap = {low_byte, high_byte};
    
    // 多层拼接
    assign concat_result = {8'hFF, data_in, 8'h00};
endmodule
