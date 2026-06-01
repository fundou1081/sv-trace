#!/usr/bin/env python3
"""可综合性测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser

CASES = [
    ("标准可综合", '''
module synth(input clk, rst, d, output reg q);
    always @(posedge clk or negedge rst) begin
        if (!rst) q <= 0;
        else q <= d;
    end
endmodule
'''),
    ("阻塞赋值可综合", '''
module blocking(input clk, a, b, output reg y);
    always @(posedge clk) begin
        y = a + b;
    end
endmodule
'''),
    ("三态门", '''
module tri_test(inout tri, input en, data);
    assign tri = en ? data : 1'bz;
endmodule
'''),
]

def main():
    print("可综合性测试")
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
