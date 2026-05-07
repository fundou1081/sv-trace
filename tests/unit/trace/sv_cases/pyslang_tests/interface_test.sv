// ============================================================================
// Interface 测试用例
// ============================================================================

// Test 1: 简单接口
interface simple_intf;
    logic [7:0] data;
    logic valid;
endinterface

// Test 2: 带时钟的接口
interface clocked_intf(input clk);
    logic [7:0] data;
    logic valid;
endinterface

// Test 3: modport
interface modport_intf;
    logic [7:0] data;
    logic valid;
    
    modport master (
        input data,
        input valid
    );
    
    modport slave (
        output data,
        output valid
    );
endinterface

// Test 4: 带有信号定义的接口
interface signal_intf;
    logic [31:0] addr;
    logic [7:0] wdata;
    logic [7:0] rdata;
    logic we;
    logic re;
endinterface
