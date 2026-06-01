#!/usr/bin/env python3
"""代码检查边界语法测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser

CASES = [
    ("priority_case", "priority case(x) 0: y=1; endcase"),
    ("unique_case", "unique case(x) 0: y=1; endcase"),
    ("casez", "casez(x) 3'b??1: y=1; endcasez"),
    ("casex", "casex(x) 3'bx?: y=1; endcasex"),
    ("generate_for", "genvar i; for(i=0;i<4;i++) begin end"),
    ("generate_if", "if (EN) begin end else begin end"),
    ("generate_case", "case(sel) 0: endcase"),
]

def main():
    print("代码检查边界语法测试")
    for name, code in CASES:
        try:
            p = SVParser()
            p.parse_text(f"module m; {code} endmodule")
            print(f"  ✅ {name}")
        except:
            print(f"  ❌ {name}")
    print(f"\n{len(CASES)} cases")
main()
