#!/usr/bin/env python3
"""OpenTitan 测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser
from trace.driver import DriverTracer

FILES = [
    '/Users/fundou/my_dv_proj/opentitan/hw/ip/uart/rtl/uart_core.sv',
    '/Users/fundou/my_dv_proj/opentitan/hw/ip/edn/rtl/edn_core.sv',
]

def main():
    passed = 0
    for fp in FILES:
        try:
            p = SVParser()
            p.parse_file(fp)
            d = DriverTracer(p)
            print(f"  ✅ {os.path.basename(os.path.dirname(fp))}: {len(d.get_drivers('*'))} drivers")
            passed += 1
        except Exception as e:
            print(f"  ❌ {os.path.basename(os.path.dirname(fp))}")
    print(f"\n{passed}/{len(FILES)} passed")
main()
