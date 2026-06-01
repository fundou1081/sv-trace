#!/usr/bin/env python3
"""代码复杂度检查测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser

CASES = [
    ("简单模块", '''
module simple(input a, output y);
    assign y = a;
endmodule
'''),
    ("中等复杂度", '''
module medium(input clk, a, b, c, d, output y);
    always @(*) begin
        if (a && b) y = c;
        else if (a) y = d;
        else y = 0;
    end
endmodule
'''),
    ("高复杂度", '''
module complex(input clk, a, b, c, d, e, f, g, h, output y);
    always @(*) begin
        if (a && b && c) y = d;
        else if (a && b) y = e;
        else if (a && c) y = f;
        else if (a) y = g;
        else y = h;
    end
endmodule
'''),
]

def main():
    print("代码复杂度检查测试")
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
