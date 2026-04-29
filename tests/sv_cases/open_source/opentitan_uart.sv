// ============================================================================
// OpenTitan UART Core - 测试用例来源
// File: opentitan/hw/ip/uart/rtl/uart_core.sv
// ============================================================================

// Test 1: 复杂端口声明 (interface 类型)
module uart_core_test #(
    parameter int NcoWidth = 16,
    parameter int TxFifoDepth = 8
) (
    input               clk_i,
    input               rst_ni,
    input  uart_reg_pkg::uart_reg2hw_t reg2hw,
    output uart_reg_pkg::uart_hw2reg_t hw2reg,
    input               rx,
    output logic         tx
);

// Test 2: import 语句
import uart_reg_pkg::*;
import prim_pkg::*;

// Test 3: typedef enum
typedef enum logic [1:0] {
    BRK_CHK  = 2'b00,
    BRK_WAIT = 2'b01,
    BRK_DONE = 2'b10
} break_state_e;

// Test 4: localparam 计算
localparam int NcoWidth = $bits(reg2hw.ctrl.nco.q);
localparam int TxFifoDepthW = $clog2(TxFifoDepth) + 1;

// Test 5: always_ff 异步复位
always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
        allzero_cnt_q <= '0;
        break_st_q <= BRK_CHK;
    end else begin
        allzero_cnt_q <= allzero_cnt_d;
        break_st_q <= break_st_next;
    end
end

// Test 6: always_comb unique case
always_comb begin
    unique case (reg2hw.ctrl.rxblvl.q)
        2'h0:    break_err = allzero_cnt_d >= 5'd2;
        2'h1:    break_err = allzero_cnt_d >= 5'd4;
        2'h2:    break_err = allzero_cnt_d >= 5'd8;
        default: break_err = allzero_cnt_d >= 5'd16;
    endcase
end

// Test 7: 复杂连续赋值
assign uart_fifo_rxrst = reg2hw.fifo_ctrl.rxrst.q;
assign hw2reg.status.rxempty.d = ~rx_fifo_rvalid;

// Test 8: 三元表达式
assign break_state_next = (event_rx_break_err) ? BRK_WAIT : BRK_CHK;

endmodule
