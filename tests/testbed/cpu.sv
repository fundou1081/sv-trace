
module CPU(
  input clk, rst_n,
  input [7:0] alu_a, alu_b,
  input alu_op_valid,
  input [2:0] alu_op,
  output [7:0] alu_result,
  output alu_result_valid,
  
  input [7:0] lsu_data, lsu_valid,
  output [7:0] lsu_result,
  output lsu_result_valid
);
  // ALU path
  always @(posedge clk) begin
    if(!rst_n) begin
      alu_result <= 0;
      alu_result_valid <= 0;
    end else if(alu_op_valid) begin
      case(alu_op)
        3'd0: alu_result <= alu_a + alu_b;  // add
        3'd1: alu_result <= alu_a - alu_b;  // sub
        3'd2: alu_result <= alu_a & alu_b;   // and
        3'd3: alu_result <= alu_a | alu_b;  // or
        default: alu_result <= alu_a;
      endcase
      alu_result_valid <= 1;
    end else
      alu_result_valid <= 0;
  end
  
  // LSU path  
  always @(posedge clk) begin
    if(!rst_n) begin
      lsu_result <= 0;
      lsu_result_valid <= 0;
    end else if(lsu_valid)
      lsu_result <= lsu_data + 1;
    else
      lsu_result_valid <= 0;
  end
endmodule
