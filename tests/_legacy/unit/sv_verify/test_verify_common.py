#!/usr/bin/env python3
"""验证常用语法测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser

CASES = [
    ("modport", "interface i; modport m(input a); endinterface"),
    ("clocking", "interface i; clocking cb @(posedge clk); endclocking endinterface"),
    ("struct", "struct {logic a; logic b;} s;"),
    ("typedef", "typedef logic [7:0] byte_t;"),
    ("enum", "enum {IDLE, RUN} st;"),
    ("union", "union {logic [7:0] b; logic [1:0] a;} u;"),
    ("packed_struct", "packed struct {logic [7:0] a;} s;"),
    ("extends", "class c extends p;"),
    ("virtual_interface", "virtual interface i;"),
    ("package_import", "import p::*;"),
]

def main():
    print("验证常用语法测试")
    for name, code in CASES:
        try:
            p = SVParser()
            p.parse_text(f"module m; {code} endmodule")
            print(f"  ✅ {name}")
        except:
            print(f"  ⚠️  {name}")
    print(f"\n{len(CASES)} cases")
main()
