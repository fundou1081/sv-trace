#!/usr/bin/env python3
"""验证边界语法测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser

CASES = [
    ("unique0", "unique case(x) 0: y=1; 1: y=2; endcase"),
    ("priority", "priority casez(x) 3'b??1: y=1; 3'b?1?: y=2; endcase"),
    ("wildcard", "casex(x) 3'b1x?: y=1; endcase"),
    ("generate_for", "genvar i; for(i=0;i<4;i=i+1) begin end"),
    ("generate_if", "if (EN) begin end else begin end"),
    ("generate_case", "case(sel) 0: endcase"),
    ("function", "function void f; endfunction"),
    ("task", "task t; endtask"),
    ("class_pkg", "package p; endpackage"),
    ("interface", "interface i; logic a; endinterface"),
]

def main():
    print("验证边界语法测试")
    for name, code in CASES:
        try:
            p = SVParser()
            p.parse_text(f"module m; {code} endmodule")
            print(f"  ✅ {name}")
        except:
            print(f"  ⚠️  {name}")
    print(f"\n{len(CASES)} cases")
main()
