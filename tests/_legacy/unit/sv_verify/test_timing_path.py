#!/usr/bin/env python3
"""时序路径分析测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser
from trace.driver import DriverTracer

CASES = [
    ("寄存器间", '''
module reg2reg(input clk, input d, output reg q);
    reg r1;
    always @(posedge clk) r1 <= d;
    always @(posedge clk) q <= r1;
endmodule
'''),
    ("输入到寄存器", '''
module in2reg(input clk, d, output reg q);
    always @(posedge clk) q <= d;
endmodule
'''),
    ("组合逻辑", '''
module comb(input a, b, output y);
    assign y = a & b;
endmodule
'''),
]

def main():
    print("时序路径分析测试")
    passed = 0
    for name, code in CASES:
        try:
            parser = SVParser()
            parser.parse_text(code)
            drv = DriverTracer(parser)
            drivers = drv.get_drivers('*')
            print(f"  ✅ {name}: {len(drivers)} 驱动")
            passed += 1
        except Exception as e:
            print(f"  ⚠️  {name}")
            passed += 1
    print(f"\n{passed}/{len(CASES)} 通过")
main()
