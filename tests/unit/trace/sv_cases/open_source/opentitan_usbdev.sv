// ============================================================================
// OpenTitan USB Device - USB 协议相关结构
// File: opentitan/hw/ip/usbdev/rtl/usbdev.sv (简化)
// ============================================================================

`include "prim_assert.sv"

module usbdev
  import usbdev_pkg::*;
  import usbdev_reg_pkg::*;
#(
  parameter int NUsbWidth = 2,
  parameter int NBuffers = 4
) (
  // Clock and reset
  input clk_i,
  input rst_ni,
  input clk_aon_i,
  input rst_aon_ni,
  
  // Bus interface
  input  tlul_pkg::tl_h2d_t tl_i,
  output tlul_pkg::tl_d2h_t tl_o,
  
  // USB pins (differential)
  input  logic       usb_rx_d_i,
  input  logic       usb_rx_dp_i,
  input  logic       usb_rx_dn_i,
  output logic       usb_tx_d_o,
  output logic       usb_tx_se0_o,
  output logic       usb_tx_dp_o,
  output logic       usb_tx_dn_o,
  output logic       usb_pullup_en_o,
  
  // Memory interface
  output logic [11:0] mem_addr_o,
  input  logic [7:0]  mem_rdata_i,
  output logic [7:0]  mem_wdata_o,
  output logic        mem_we_o,
  output logic        mem_req_o,
  
  // Interrupts
  output logic intr_pkt_received_o,
  output logic intr_pkt_sent_o,
  output logic intr_av_empty_o,
  output logic intr_frame_o,
  output logic intr_link_reset_o,
  output logic intr_host_lost_o,
  
  // Alerts
  input  prim_alert_pkg::alert_rx_t [NumAlerts-1:0] alert_rx_i,
  output prim_alert_pkg::alert_tx_t [NumAlerts-1:0] alert_tx_o
);

  // USB PID definitions
  typedef enum logic [3:0] {
    // Token PIDs
    USB_pid_oSETUP = 4'b1101,
    USB_pid_oIN    = 4'b1001,
    USB_pid_oOUT   = 4'b0001,
    USB_pid_oPING  = 4'b0101,
    // Data PIDs
    USB_pid_oDATA0 = 4'b0011,
    USB_pid_oDATA1 = 4'b1011,
    USB_pid_oDATA2 = 4'b0111,
    // Handshake PIDs
    USB_pid_oACK   = 4'b0010,
    USB_pid_oNAK   = 4'b1010,
    USB_pid_oSTALL = 4'b1110,
    USB_pid_oNYET  = 4'b0110
  } usb_pid_e;

  // USB state machine
  typedef enum logic [2:0] {
    USB_ST_DISCONN = 3'h0,
    USB_ST_RESET    = 3'h1,
    USB_ST_CONFIG   = 3'h2,
    USB_ST_DEFAULT  = 3'h3,
    USB_ST_ADDRESSED= 3'h4,
    USB_ST_CONFIGURED= 3'h5,
    USB_ST_SUSPEND  = 3'h6
  } usb_state_e;

  // Local signals
  usb_state_e state_q, state_d;
  logic [NUsbWidth-1:0] usb_p, usb_n;
  logic [6:0] dev_addr_q;
  logic [3:0] out_ep_pending;
  logic [11:0] frame_cnt;
  
  // Buffer signals
  logic [7:0] out_buf_data;
  logic [11:0] out_buf_addr;
  logic out_buf_we;
  
  // USB differential receiver
  always_comb begin
    usb_p = usb_rx_d_i;
    usb_n = 1'b0;
  end
  
  // CRC calculation
  logic [15:0] crc16_out;
  logic [7:0] crc5_out;
  
  // always_ff for state register
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      state_q <= USB_ST_DISCONN;
      dev_addr_q <= 7'h0;
      frame_cnt <= 12'h0;
    end else begin
      state_q <= state_d;
      if (state_d == USB_ST_DEFAULT)
        dev_addr_q <= 7'h0;
    end
  end
  
  // USB FSM
  always_comb begin
    state_d = state_q;
    unique case (state_q)
      USB_ST_DISCONN: if (usb_rx_d_i) state_d = USB_ST_RESET;
      USB_ST_RESET:    state_d = USB_ST_DEFAULT;
      USB_ST_DEFAULT:  if (out_ep_pending != 0) state_d = USB_ST_ADDRESSED;
      default: state_d = state_q;
    endcase
  end
  
  // Covergroup for USB protocol coverage
  covergroup usb_protocol_cg @(posedge clk_i);
    coverpoint state_q;
    coverpoint usb_pid_e'(out_buf_data[3:0]);
    cross state_q, usb_pid_e'(out_buf_data[3:0]);
  endgroup
  
  usb_protocol_cg u_protocol_cg = new();

  // Protocol assertion
  `ASSERT(validStateTransition_A, 
    $changed(state_q) |-> !$isunknown(state_q), clk_i, rst_ni)

endmodule
