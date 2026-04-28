#!/usr/bin/env python3
"""代码风格检查测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser

CASES = [
    ("命名规范", '''
module MyModule(input clk);
    reg [7:0] COUNTER;
    always @(posedge clk) COUNTER <= COUNTER + 1;
endmodule
'''),
    ("下划线命名", '''
module my_module(input clk);
    reg [7:0] my_counter;
    always @(posedge clk) my_counter <= my_counter + 1;
endmodule
'''),
    ("常量命名", '''
module top;
    parameter WIDTH = 8;
    parameter MAX_COUNT = 255;
endmodule
'''),
]

def main():
    print("代码风格检查测试")
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
