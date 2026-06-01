#!/usr/bin/env python3
"""边界语法测试 - Corner Cases"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser
from trace.driver import DriverTracer

CASES = [
    # 1. 多种case类型
    ("priority_case", '''
module pc(input [1:0] s, output [7:0] y);
    priority case(s)
        2'b00: y = 1;
        2'b01: y = 2;
        2'b10: y = 3;
        default: y = 0;
    endcase
endmodule
'''),
    ("unique_case", '''
module uc(input [1:0] s, output [7:0] y);
    unique case(s)
        0: y = 1;
        1: y = 2;
        default: y = 0;
    endcase
endmodule
'''),
    ("casez", '''
module cz(input [2:0] s, output y);
    casez(s)
        3'b??1: y = 1;
        3'b?1?: y = 2;
        default: y = 0;
    endcasez
endmodule
'''),
    ("casex", '''
module cx(input [2:0] s, output y);
    casex(s)
        3'bxx1: y = 1;
        default: y = 0;
    endcasex
endmodule
'''),
    # 2. 复杂条件
    ("ternary_nested", '''
module tn(input [1:0] a, b, c, output y);
    assign y = a[0] ? (b[0] ? c[0] : c[1]) : (b[1] ? c[2] : c[3]);
endmodule
'''),
    ("wildcard_case", '''
module wc(input [2:0] s, output y);
    casez(s)
        3'b1??: y = 1;
        3'b01?: y = 2;
        default: y = 0;
    endcase
endmodule
'''),
    # 3. 特殊赋值
    ("assign_with_select", '''
module aws(input [3:0] a, sel, output y);
    assign y = sel ? a[3:2] : a[1:0];
endmodule
'''),
    ("concat_assignment", '''
module ca(input a, b, c, d, output [3:0] y);
    assign y = {a, b, c, d};
endmodule
'''),
    ("part_select", '''
module ps(input [7:0] a, output [3:0] y);
    assign y = a[3+:4];
endmodule
'''),
    ("signed_assignment", '''
module sa(input [7:0] a, b, output signed [7:0] y);
    assign y = $signed(a) + $signed(b);
endmodule
'''),
]

def main():
    print("边界语法测试")
    passed = 0
    for name, code in CASES:
        try:
            p = SVParser()
            p.parse_text(code)
            d = DriverTracer(p)
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}")
    print(f"\n{passed}/{len(CASES)} 通过")
main()
