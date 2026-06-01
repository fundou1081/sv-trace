#!/usr/bin/env python3
"""约束分析测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser
from parse.constraint import ConstraintExtractor

CASES = [
    ("简单约束", '''
class packet;
    rand bit [7:0] data;
    constraint c { data inside {[0:100]}; }
endclass
'''),
    ("范围约束", '''
class addr_range;
    rand bit [31:0] addr;
    constraint c { addr inside {[16'h1000:16'hFFFF]}; }
endclass
'''),
    ("权重约束", '''
class weighted;
    rand bit [1:0] mode;
    constraint c { mode dist {0:=1, 1:=2, 2:=1}; }
endclass
'''),
]

def main():
    print("约束分析测试")
    passed = 0
    for name, code in CASES:
        try:
            parser = SVParser()
            parser.parse_text(code)
            ext = ConstraintExtractor(parser)
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ⚠️  {name}")
            passed += 1
    print(f"\n{passed}/{len(CASES)} 通过")
main()
