// ============================================================================
// OpenTitan SPI Device - 复杂端口声明测试用例
// File: opentitan/hw/ip/spi_device/rtl/spi_device.sv (简化)
// ============================================================================

// Test 1: 参数化模块
module spi_device #(
    parameter int NumAlerts = 1,
    parameter int unsigned AlertSkewCycles = 1,
    parameter bit EnableRacl = 1'b0
) (
    // 时钟和复位
    input clk_i,
    input rst_ni,

    // Register interface
    input  tlul_pkg::tl_h2d_t tl_i,
    output tlul_pkg::tl_d2h_t tl_o,

    // Alerts
    input  prim_alert_pkg::alert_rx_t [NumAlerts-1:0] alert_rx_i,
    output prim_alert_pkg::alert_tx_t [NumAlerts-1:0] alert_tx_o,

    // SPI Interface
    input              cio_sck_i,
    input              cio_csb_i,
    output logic [3:0] cio_sd_o,
    output logic [3:0] cio_sd_en_o,
    input        [3:0] cio_sd_i,

    // Interrupts
    output logic intr_upload_cmdfifo_not_empty_o,
    output logic intr_readbuf_watermark_o,

    // DFT
    input mbist_en_i,
    input scan_clk_i,
    input scan_rst_ni
);

// Test 2: 端口数组
localparam int RaclWidth = 10;
input  [RaclWidth-1:0] racl_policies_i [73];
output [RaclWidth-1:0] racl_error_o;

// Test 3: interface 端口
input  spi_device_pkg::passthrough_req_t passthrough_o;
output spi_device_pkg::passthrough_rsp_t passthrough_i;

endmodule
