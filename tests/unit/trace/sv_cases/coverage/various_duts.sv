// Test 1: FIFO interface
module fifo DUT (
    input  clk,
    input  rst_n,
    input  [7:0] wr_data,
    input         wr_en,
    input         rd_en,
    output [7:0] rd_data,
    output       full,
    output       empty
);
    // ...
endmodule

// Test 2: AXI Stream
module axis_slave (
    input        aclk,
    input        aresetn,
    input  [7:0] s_axis_tdata,
    input        s_axis_tvalid,
    output       s_axis_tready,
    output [7:0] m_axis_tdata,
    output       m_axis_tvalid,
    input        m_axis_tready
);
    // ...
endmodule

// Test 3: APB
module apb_slave (
    input        pclk,
    input        presetn,
    input  [7:0] paddr,
    input        psel,
    input        penable,
    input        pwrite,
    input  [7:0] pwdata,
    output [7:0] prdata,
    output       pready
);
    // ...
endmodule
