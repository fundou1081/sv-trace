#!/usr/bin/env python3
"""静态分析测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser

CASES = [
    ("组合逻辑", '''
module comb(input a, b, output y);
    assign y = a ^ b;
endmodule
'''),
    ("时序逻辑", '''
module seq(input clk, d, output reg q);
    always @(posedge clk) q <= d;
endmodule
'''),
    ("混合逻辑", '''
module mixed(input clk, a, b, output reg q, y);
    always @(posedge clk) q <= a;
    assign y = q & b;
endmodule
'''),
]

def main():
    print("静态分析测试")
    passed = 0
    for name, code in CASES:
        try:
            parser = SVParser()
            parser.parse_text(code)
            print(f"  ✅ {name}")
            passed += 1
        except:
            print(f"  ❌ {name}")
    print(f"\n{passed}/{len(CASES)} 通过")
main()
