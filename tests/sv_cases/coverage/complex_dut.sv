module complex_dut (
    input        clk,
    input        rst_n,
    input  [7:0] pkt_data,
    input        pkt_valid,
    input        pkt_ready,
    input  [2:0] pkt_type,
    input  [3:0] pkt_id,
    
    output [7:0] rsp_data,
    output       rsp_valid,
    output       rsp_ready
);
    // ... design logic ...
endmodule
