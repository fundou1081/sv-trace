// ============================================================================
// OpenTitan RV_DM - 复杂 SystemVerilog 语法
// File: opentitan/hw/ip/rv_dm/rtl/rv_dm.sv
// ============================================================================

`include "prim_assert.sv"

module rv_dm
  import rv_dm_reg_pkg::*;
#(
  parameter logic [NumAlerts-1:0]  AlertAsyncOn = {NumAlerts{1'b1}},
  parameter int unsigned          AlertSkewCycles = 1,
  parameter logic [31:0]         IdcodeValue = 32'h00000001,
  parameter bit                  UseDmiInterface = 1'b0,
  // Parameter array
  parameter bit [7:0]            RaclPolicySelVecRegs[8] = '{8{1'b0}}
) (
  input  logic                clk_i,
  input  logic                rst_ni,
  input  logic [31:0]         next_dm_addr_i,
  input  lc_ctrl_pkg::lc_tx_t lc_hw_debug_clr_i,
  input  lc_ctrl_pkg::lc_tx_t lc_hw_debug_en_i,
  input  lc_ctrl_pkg::lc_tx_t lc_dft_en_i,
  input  prim_mubi_pkg::mubi4_t scanmode_i,
  output logic                ndmreset_req_o,
  output logic                dmactive_o,
  input  tlul_pkg::tl_h2d_t  regs_tl_d_i,
  output tlul_pkg::tl_d2h_t  regs_tl_d_o,
  input  tlul_pkg::tl_h2d_t  mem_tl_d_i,
  output tlul_pkg::tl_d2h_t  mem_tl_d_o,
  output tlul_pkg::tl_h2d_t  sba_tl_h_o,
  input  tlul_pkg::tl_d2h_t  sba_tl_h_i
);

  // Import statements
  import prim_mubi_pkg::mubi4_test_true_strict;
  import lc_ctrl_pkg::lc_tx_test_true_strict;

  // Parameter assertion
  `ASSERT_INIT(paramCheckNumHarts, NrHarts > 0)

  // Static hartinfo
  localparam dm::hartinfo_t DebugHartInfo = '{
    zero1:      '0,
    nscratch:   2,
    zero0:      0,
    dataaccess: 1'b1,
    datasize:   dm::DataCount,
    dataaddr:   dm::DataAddr
  };

  // Generate block with genvar
  dm::hartinfo_t [NrHarts-1:0] hartinfo;
  for (genvar i = 0; i < NrHarts; i++) begin : gen_dm_hart_ctrl
    assign hartinfo[i] = DebugHartInfo;
  end

  // Localparam with struct
  localparam int BusWidth = 32;

  // Logic arrays
  logic [31:0] debug_req;
  logic [NrHarts-1:0] unavailable;

  // Always_ff with async reset
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      dmactive_o <= 1'b0;
      ndmreset_req_o <= 1'b0;
    end else begin
      dmactive_o <= 1'b1;
      ndmreset_req_o <= ndmreset_req_d;
    end
  end

  // Always_comb
  always_comb begin
    automatic logic [NrHarts-1:0] req = '0;
    req[0] = debug_req[0];
  end

endmodule
