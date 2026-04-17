"""
基本解析测试
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parse import SVParser


def test_basic_parse():
    """测试基本解析"""
    code = '''
module test (
    input wire clk,
    input wire rst_n,
    output reg [7:0] data
);
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data <= 8'd0;
        else
            data <= data + 1;
    end
endmodule
'''
    
    parser = SVParser()
    tree = parser.parse_text(code)
    
    print("✓ Parse succeeded")
    print(f"Module: {tree.root}")
    
    # 检查模块
    modules = parser.get_modules()
    print(f"Found {len(modules)} module(s)")
    
    return True


def test_signal_extract():
    """测试信号提取"""
    from parse import SignalExtractor
    
    code = '''
module mem (
    input wire clk,
    input wire [7:0] data_in,
    output reg [7:0] data_out
);
    
    reg [7:0] mem [0:255];
endmodule
'''
    
    parser = SVParser()
    tree = parser.parse_text(code)
    
    signals = SignalExtractor.extract(tree)
    print(f"Found {len(signals)} signal(s): {signals}")
    
    return True


if __name__ == "__main__":
    print("Running tests...")
    test_basic_parse()
    test_signal_extract()
    print("All tests passed!")
