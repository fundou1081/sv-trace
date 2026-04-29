// ============================================================================
// OpenTitan HMAC - import/include 测试用例
// File: opentitan/hw/ip/hmac/rtl/hmac.sv
// ============================================================================

`include "prim_assert.sv"

module hmac
  import prim_sha2_pkg::*;
  import hmac_reg_pkg::*;
#(
  parameter logic [NumAlerts-1:0] AlertAsyncOn = {NumAlerts{1'b1}},
  parameter int unsigned AlertSkewCycles = 1
) (
  input clk_i,
  input rst_ni,

  input  tlul_pkg::tl_h2d_t tl_i,
  output tlul_pkg::tl_d2h_t tl_o,

  input  prim_alert_pkg::alert_rx_t [NumAlerts-1:0] alert_rx_i,
  output prim_alert_pkg::alert_tx_t [NumAlerts-1:0] alert_tx_o,

  output logic intr_hmac_done_o,
  output logic intr_fifo_empty_o,
  output logic intr_hmac_err_o,
  output prim_mubi_pkg::mubi4_t idle_o
);

  // Signal declarations
  hmac_reg2hw_t reg2hw;
  hmac_hw2reg_t hw2reg;
  logic [1023:0] secret_key;
  key_length_e key_length_supplied, key_length;
  logic wipe_secret;
  logic [31:0] wipe_v;

  // FIFO signals
  logic fifo_rvalid, fifo_rready;
  sha_fifo32_t fifo_rdata;
  logic fifo_wvalid, fifo_wready;
  sha_fifo32_t fifo_wdata;

  // typedef enum
  typedef enum logic [2:0] {
    IDLE       = 3'b000,
    RECEIVE    = 3'b001,
    PAD        = 3'b010,
    COMPUTE    = 3'b011,
    DONE       = 3'b100
  } hmac_state_e;

  hmac_state_e state_q, state_d;

  // always_ff with synchronous reset
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      state_q <= IDLE;
    end else begin
      state_q <= state_d;
    end
  end

  // always_comb
  always_comb begin
    state_d = state_q;
    unique case (state_q)
      IDLE:    if (reg2hw.cmd.start.q) state_d = RECEIVE;
      RECEIVE: if (fifo_full) state_d = PAD;
      PAD:     state_d = COMPUTE;
      COMPUTE: if (hmac_done) state_d = DONE;
      DONE:    state_d = IDLE;
      default: state_d = IDLE;
    endcase
  end

  // Assertion example
  `ASSERT(StateValid_A, $onehot0(state_q), clk_i, rst_ni)

endmodule
