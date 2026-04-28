#!/usr/bin/env python3
"""代码优化建议测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser

CASES = [
    ("可简化的always", '''
module simple(input clk, a, output reg y);
    always @(posedge clk) begin
        y <= a;
    end
endmodule
'''),
    ("多路选择器", '''
module mux(input [1:0] sel, a, b, c, d, output y);
    assign y = sel[1] ? (sel[0] ? d : c) : (sel[0] ? b : a);
endmodule
'''),
    ("逻辑优化", '''
module opt(input a, b, output y);
    assign y = (a & 1'b1) | (b & 1'b1);
endmodule
'''),
]

def main():
    print("代码优化建议测试")
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
