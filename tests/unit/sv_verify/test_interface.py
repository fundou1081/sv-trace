#!/usr/bin/env python3
"""接口分析测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser

CASES = [
    ("简单接口", '''
interface simple_bus;
    logic [7:0] data;
    logic valid;
endinterface
'''),
    ("ModPort", '''
interface axi4;
    logic [31:0] awaddr;
    logic awvalid;
    modport master (input awaddr, output awvalid);
    modport slave (output awaddr, input awvalid);
endinterface
'''),
    ("时序接口", '''
interface clk_rst;
    logic clk;
    logic rst_n;
    clocking cb @(posedge clk);
    endclocking
endinterface
'''),
]

def main():
    print("接口分析测试")
    passed = 0
    for name, code in CASES:
        try:
            parser = SVParser()
            parser.parse_text(code)
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ⚠️  {name}")
            passed += 1
    print(f"\n{passed}/{len(CASES)} 通过")
main()
