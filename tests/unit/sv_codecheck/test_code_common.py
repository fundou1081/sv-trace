#!/usr/bin/env python3
"""代码检查常用语法测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser

CASES = [
    ("struct", "struct {logic a;} s;"),
    ("typedef", "typedef logic [7:0] byte_t;"),
    ("enum", "enum {IDLE, RUN} st;"),
    ("function", "function void f; endfunction"),
    ("task", "task t; endtask"),
    ("class", "class c; endclass"),
    ("interface", "interface i; endinterface"),
    ("modport", "interface i; modport m(input a); endinterface"),
    ("clocking", "interface i; clocking cb; endclocking endinterface"),
    ("package", "package p; endpackage"),
]

def main():
    print("代码检查常用语法测试")
    for name, code in CASES:
        try:
            p = SVParser()
            p.parse_text(f"module m; {code} endmodule")
            print(f"  ✅ {name}")
        except:
            print(f"  ❌ {name}")
    print(f"\n{len(CASES)} cases")
main()
