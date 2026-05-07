// ============================================================================
// Struct/Union 测试用例
// ============================================================================

// Test 1: 简单结构体
module struct_simple;
    typedef struct {
        logic [7:0] addr;
        logic [7:0] data;
        logic we;
    } mem_req_t;
    
    mem_req_t req;
endmodule

// Test 2: 打包结构体
module struct_packed;
    typedef struct packed {
        logic [15:0] addr;
        logic [7:0] data;
        logic valid;
    } packet_t;
    
    packet_t pkt;
endmodule

// Test 3: 联合体
module union_test;
    typedef union {
        logic [31:0] data;
        struct {
            logic [15:0] low;
            logic [15:0] high;
        } parts;
    } converter_t;
    
    converter_t conv;
endmodule
