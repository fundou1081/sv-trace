// ============================================================================
// OpenTitan AES Package - 复杂 SystemVerilog 类型和参数
// File: opentitan/hw/ip/aes/rtl/aes_pkg.sv (简化)
// ============================================================================

package aes_pkg;

  // Test 1: parameter 复杂计算
  parameter int unsigned SliceSizeCtr = 16;
  parameter int unsigned NumSlicesCtr = 32 / SliceSizeCtr;
  parameter int unsigned SliceIdxWidth = 4;

  // Test 2: typedef logic 数组
  typedef logic [63:0] clearing_lfsr_seed_t;
  typedef logic [63:0][5:0] clearing_lfsr_perm_t;

  // Test 3: parameter 多维数组
  parameter clearing_lfsr_seed_t RndCnstClearingLfsrSeedDefault = 64'hc32d580f74f1713a;

  // Test 4: typedef enum
  typedef enum integer {
    SBoxImplLut,
    SBoxImplCanright,
    SBoxImplCanrightMasked,
    SBoxImplMaskedNoreconfigCanrightMasked,
    SBoxImplMaskedNoreconfigCanright
  } sbox_impl_e;

  // Test 5: typedef struct
  typedef struct packed {
    logic [3:0] mode;
    logic [7:0] key_len;
    logic [7:0] prng_reseed;
  } aes_cipher_ctrl_reg_t;

  // Test 6: localparam 复杂表达式
  localparam int WidthPRDSBox = 8;
  localparam int WidthPRDData = 16 * WidthPRDSBox;
  localparam int WidthPRDMasking = WidthPRDData + WidthPRDData;

  // Test 7: typedef union
  typedef union packed {
    logic [31:0] word;
    logic [7:0] bytes [4];
  } aes_word_t;

  // Test 8: 多维 logic
  typedef logic [3:0] [7:0] aes_state_t;

endpackage

// Test 9: 在 module 中使用 package 的类型
module aes_core
  import aes_pkg::*;
  (
    input  logic             clk_i,
    input  logic             rst_ni,
    input  sbox_impl_e       sbox_impl_i,
    input  aes_state_t       state_i,
    output aes_state_t       state_o
);

  // 使用 package 中的类型
  aes_word_t data_word;
  clearing_lfsr_seed_t seed;
  logic [WidthPRDMasking-1:0] prng_mask;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      prng_mask <= '0;
    end else begin
      prng_mask <= {1'b1, prng_mask[WidthPRDMasking-1:1]};
    end
  end

endmodule
