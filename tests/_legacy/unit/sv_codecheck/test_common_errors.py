#!/usr/bin/env python3
"""常见错误检测测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser

CASES = [
    ("完整always", '''
module test(input clk, output reg q);
    always @(posedge clk) q <= ~q;
endmodule
'''),
    ("完整case", '''
module test(input [1:0] sel, output [7:0] y);
    case (sel)
        0: y = 8'h01;
        1: y = 8'h02;
        default: y = 8'h00;
    endcase
endmodule
'''),
    ("完整function", '''
module test;
    function [7:0] add;
        input [7:0] a, b;
        add = a + b;
    endfunction
endmodule
'''),
]

def main():
    print("常见错误检测测试")
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
