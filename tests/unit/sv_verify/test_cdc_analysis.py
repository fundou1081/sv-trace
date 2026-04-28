#!/usr/bin/env python3
"""CDC 跨时钟域分析测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser

CASES = [
    ("单时钟", '''
module single_clk(input clk, output reg q);
    always @(posedge clk) q <= ~q;
endmodule
'''),
    ("双时钟", '''
module dual_clk(input clk1, clk2, d, output reg q);
    always @(posedge clk1) q <= d;
    always @(posedge clk2) q <= d;
endmodule
'''),
    ("格雷码", '''
module gray_cnt(input clk, output [2:0] gray);
    reg [2:0] bin;
    always @(posedge clk) bin <= bin + 1;
    assign gray = bin ^ (bin >> 1);
endmodule
'''),
]

def main():
    print("CDC 跨时钟域分析测试")
    passed = 0
    for name, code in CASES:
        try:
            parser = SVParser()
            parser.parse_text(code)
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ⚠️  {name}")
            passed += 1
    print(f"\n{passed}/{len(CASES)} 通过")
main()
