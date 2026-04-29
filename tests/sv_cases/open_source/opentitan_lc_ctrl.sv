// ============================================================================
// OpenTitan Life Cycle Controller - 多时钟域和复杂接口
// File: opentitan/hw/ip/lc_ctrl/rtl/lc_ctrl.sv (简化)
// ============================================================================

`include "prim_assert.sv"

module lc_ctrl
  import lc_ctrl_pkg::*;
  import lc_ctrl_reg_pkg::*;
#(
  parameter bit [7:0]  ProductId = '0,
  parameter logic [31:0] IdcodeValue = 32'h00000001,
  parameter int unsigned EscNumSeverities = 4,
  parameter int unsigned EscPingCountWidth = 16,
  parameter logic [31:0] RndCnstLcKeymgrDivInvalid = 32'h12345678,
  // Parameter with conditional
  parameter bit SecVolatileRawUnlockEn = 0
) (
  // Main clock
  input clk_i,
  input rst_ni,
  // KMAC clock domain
  input clk_kmac_i,
  input rst_kmac_ni,
  
  // Bus interface
  input  tlul_pkg::tl_h2d_t regs_tl_i,
  output tlul_pkg::tl_d2h_t regs_tl_o,
  
  // DMI interface
  input  tlul_pkg::tl_h2d_t dmi_tl_i,
  output tlul_pkg::tl_d2h_t dmi_tl_o,
  
  // JTAG interface
  input  jtag_pkg::jtag_req_t jtag_i,
  output jtag_pkg::jtag_rsp_t jtag_o,
  
  // Scan mode
  input scan_rst_ni,
  input prim_mubi_pkg::mubi4_t scanmode_i,
  
  // Alerts
  input  prim_alert_pkg::alert_rx_t [NumAlerts-1:0] alert_rx_i,
  output prim_alert_pkg::alert_tx_t [NumAlerts-1:0] alert_tx_o,
  
  // Escalation
  input  prim_esc_pkg::esc_rx_t esc_scrap_state0_tx_i,
  output prim_esc_pkg::esc_tx_t esc_scrap_state0_rx_o,
  input  prim_esc_pkg::esc_rx_t esc_scrap_state1_tx_i,
  output prim_esc_pkg::esc_tx_t esc_scrap_state1_rx_o,
  
  // Power manager
  input  pwr_lc_req_t pwr_lc_i,
  output pwr_lc_rsp_t pwr_lc_o,
  
  // OTP program interface
  output otp_ctrl_pkg::lc_otp_program_req_t lc_otp_program_o,
  input  otp_ctrl_pkg::lc_otp_program_rsp_t lc_otp_program_i
);

  // Life cycle state typedef
  typedef enum logic [5:0] {
    LcStRawIntern      = 6'b000001,
    LcStScrap          = 6'b111110,
    LcStPostAmp1Adv1   = 6'b001001,
    LcStPostModem5Adv4 = 6'b011101,
    LcStRma            = 6'b011110
  } lc_state_e;

  // Transition target typedef  
  typedef enum logic [5:0] {
    LcTargetRawIntern      = 6'b000001,
    LcTargetTestLocked0    = 6'b001010,
    LcTargetRma            = 6'b011110
  } lc_transition_target_e;

  // Token typedef
  typedef logic [31:0] token_t [4];
  
  // Local signals
  lc_state_e state_q, state_d;
  lc_transition_target_e transition_target;
  token_t hashed_token;
  logic [5:0] transition_count_q;
  logic [15:0] escalate_cnt_q;
  
  // Multi-clock signals
  logic [31:0] kmac_data_rdy;
  logic [31:0] otp_program_req;
  
  // Mubi type signals
  prim_mubi_pkg::mubi4_t if_empty, if_full;
  
  // Generate for alert senders
  for (genvar i = 0; i < NumAlerts; i++) begin : gen_alert
    prim_alert_sender #(
      .PingCntWidth(EscPingCountWidth),
      .PingOkCycles(1),
      .PingFailCycles(1)
    ) u_alert_sender (
      .clk_i(clk_i),
      .rst_ni(rst_ni),
      .alert_rx_i(alert_rx_i[i]),
      .alert_tx_o(alert_tx_o[i])
    );
  end

  // Clock gating cell
  prim_clock_gating #(
    .NoTestClkScan(1'b1)
  ) u_clock_gating (
    .clk_i(clk_i),
    .en_i(enable),
    .test_en_i(scanmode_i == prim_mubi_pkg::MuBi4True),
    .clk_o(gated_clk)
  );

  // always_ff for state machine
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      state_q <= LcStRawIntern;
      transition_count_q <= '0;
      escalate_cnt_q <= '0;
    end else begin
      state_q <= state_d;
      if (state_q != state_d)
        transition_count_q <= transition_count_q + 1;
      
      if (|esc_scrap_state0_tx_i.p)
        escalate_cnt_q <= escalate_cnt_q + 1;
    end
  end

  // always_comb for FSM
  always_comb begin
    state_d = state_q;
    unique case (1'b1)
      state_q inside {LcStRawIntern}: begin
        if (transition_req && transition_target == LcTargetTestLocked0)
          state_d = LcStScrap;
      end
      default: state_d = LcStScrap;
    endcase
  end

  // Covergroup for coverage
  covergroup transition_cg @(posedge clk_i);
    coverpoint state_q;
    coverpoint transition_target;
    cross state_q, transition_target;
  endgroup

endmodule
