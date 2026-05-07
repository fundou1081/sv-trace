// ============================================================================
// OpenTitan Key Manager - 复杂接口和参数
// File: opentitan/hw/ip/keymgr/rtl/keymgr.sv (简化)
// ============================================================================

`include "prim_assert.sv"

module keymgr
  import keymgr_pkg::*;
  import keymgr_reg_pkg::*;
#(
  // Complex parameter with struct default
  parameter seed_t RndCnstRevisionSeed = RndCnstRevisionSeedDefault,
  parameter seed_t RndCnstCreatorIdentitySeed = RndCnstCreatorIdentitySeedDefault,
  parameter seed_t RndCnstOwnerIntIdentitySeed = RndCnstOwnerIntIdentitySeedDefault,
  parameter rand_perm_t RndCnstRandPerm = RndCnstRandPermDefault,
  
  // Parameter with complex type
  parameter lfsr_seed_t RndCnstLfsrSeed = RndCnstLfsrSeedDefault,
  parameter lfsr_perm_t RndCnstLfsrPerm = RndCnstLfsrPermDefault,
  
  // Number of cycles for skew tolerance
  parameter int unsigned AlertSkewCycles = 1
) (
  // Clock and reset
  input clk_i,
  input rst_ni,
  input rst_shadowed_ni,
  input clk_edn_i,
  input rst_edn_ni,

  // Bus Interface (struct typed)
  input  tlul_pkg::tl_h2d_t tl_i,
  output tlul_pkg::tl_d2h_t tl_o,

  // Key interface to crypto modules (complex struct)
  output hw_key_req_t aes_key_o,
  output hw_key_req_t kmac_key_o,
  output otbn_key_req_t otbn_key_o,

  // Data interface (app req/resp pattern)
  output kmac_pkg::app_req_t kmac_data_o,
  input  kmac_pkg::app_rsp_t kmac_data_i,

  // Life cycle signals (mubi type)
  input lc_ctrl_pkg::lc_tx_t lc_keymgr_en_i,
  input lc_ctrl_pkg::lc_keymgr_div_t lc_keymgr_div_i,
  
  // OTP interface (complex struct)
  input otp_ctrl_pkg::otp_keymgr_key_t otp_key_i,
  input otp_ctrl_pkg::otp_device_id_t otp_device_id_i,
  
  // Flash interface
  input flash_ctrl_pkg::keymgr_flash_t flash_i,

  // EDN interface
  output edn_pkg::edn_req_t edn_o,
  input  edn_pkg::edn_rsp_t edn_i,

  // ROM digest
  input rom_ctrl_pkg::keymgr_data_t rom_digest_i,

  // Interrupts and alerts
  output logic intr_op_done_o,
  input  prim_alert_pkg::alert_rx_t [keymgr_reg_pkg::NumAlerts-1:0] alert_rx_i,
  output prim_alert_pkg::alert_tx_t [keymgr_reg_pkg::NumAlerts-1:0] alert_tx_o
);

  // Typedef for state
  typedef enum logic [3:0] {
    StReset = 4'b0000,
    StInit = 4'b0001,
    StCreatorKey = 4'b0011,
    StOwnerKey = 4'b0111,
    StDisable = 4'b1111
  } state_e;

  // Local signals
  state_e state_q, state_d;
  logic [3:0] operation_q;
  logic advance;
  
  // Complex struct assignment
  hw_key_req_t aes_key_d, aes_key_q;
  
  // Mubi type signals
  logic [3:0] mubi_sel;
  
  // Generate for multiple instances
  for (genvar i = 0; i < keymgr_reg_pkg::NumAlerts; i++) begin : gen_alert
    prim_alert_sender #(
      .PayloadWidth(keymgr_reg_pkg::NumAlerts)
    ) u_alert_sender (
      .clk_i,
      .rst_ni,
      .alert_rx_i(alert_rx_i[i]),
      .alert_tx_o(alert_tx_o[i])
    );
  end

  // always_ff with shadowed reset
  always_ff @(posedge clk_i or negedge rst_ni or negedge rst_shadowed_ni) begin
    if (!rst_ni || !rst_shadowed_ni) begin
      state_q <= StReset;
      operation_q <= 4'b0;
    end else begin
      state_q <= state_d;
      if (advance)
        operation_q <= operation_q + 1;
    end
  end

  // FSM with unique case
  always_comb begin
    state_d = state_q;
    unique case (state_q)
      StReset:    if (lc_keymgr_en_i == lc_ctrl_pkg::On) state_d = StInit;
      StInit:     state_d = StCreatorKey;
      StCreatorKey: state_d = StOwnerKey;
      StOwnerKey:  state_d = StDisable;
      StDisable:   state_d = StDisable;
      default:    state_d = StReset;
    endcase
  end

  // Covergroup for state coverage
  covergroup state_cg @(posedge clk_i);
    coverpoint state_q;
  endgroup

  state_cg u_state_cg = new();

  // Property for state transition
  `ASSERTKnvalidStateTransition_A, 
    $changed(state_q) && state_q != StDisable
    |=>
    $past(state_q) != StReset throughout 1'b1[*1:$])

endmodule
