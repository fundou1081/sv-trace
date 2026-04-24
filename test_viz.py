import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.visualize import visualize_datapath, visualize_controlflow

# 测试数据流可视化
TEST1 = '''module pipe;
    logic [31:0] din, s1, s2, dout;
    logic clk;
    always_ff @(posedge clk) begin
        s1 <= din;
        s2 <= s1;
        dout <= s2;
    end
endmodule'''

# 测试控制流可视化
TEST2 = '''module fsm;
    logic clk;
    logic [1:0] state, next_state;
    logic req, ack;
    always_ff @(posedge clk) begin
        state <= next_state;
    end
    always_comb begin
        case(state)
            2'b00: next_state = req ? 2'b01 : 2'b00;
            2'b01: next_state = ack ? 2'b10 : 2'b01;
            default: next_state = 2'b00;
        endcase
    end
endmodule'''

print("="*60)
print("数据流可视化测试")
print("="*60)

with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
    f.write(TEST1)
    tmp = f.name

try:
    parser = SVParser()
    parser.parse_file(tmp)
    
    print("\n--- 数据流 DOT ---")
    dot = visualize_datapath(parser, 'dout')
    print(dot)
    
finally:
    os.unlink(tmp)

print("\n" + "="*60)
print("控制流可视化测试")
print("="*60)

with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
    f.write(TEST2)
    tmp = f.name

try:
    parser = SVParser()
    parser.parse_file(tmp)
    
    print("\n--- 控制流 DOT ---")
    dot = visualize_controlflow(parser, 'next_state')
    print(dot)
    
finally:
    os.unlink(tmp)
