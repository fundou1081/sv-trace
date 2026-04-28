#!/usr/bin/env python3
"""
OpenTitan 项目 sv_ast 测试
"""
import sys
import os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser


OPEN_TITAN_RTL = [
    '/Users/fundou/my_dv_proj/opentitan/hw/ip/uart/rtl/uart_core.sv',
    '/Users/fundou/my_dv_proj/opentitan/hw/ip/edn/rtl/edn_core.sv',
    '/Users/fundou/my_dv_proj/opentitan/hw/ip/prim_xilinx_ultrascale/rtl/prim_xor2.sv',
    '/Users/fundou/my_dv_proj/opentitan/hw/ip/prim_generic/rtl/prim_buf.sv',
    '/Users/fundou/my_dv_proj/opentitan/hw/ip/rv_core_ibex/rtl/rv_core_ibex.sv',
]


def main():
    print("============================================================")
    print("OpenTitan sv_ast 测试")
    print("============================================================")
    
    passed = 0
    for filepath in OPEN_TITAN_RTL:
        name = os.path.basename(os.path.dirname(filepath))
        try:
            parser = SVParser()
            parser.parse_file(filepath)
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {str(e)[:30]}")
    
    print(f"\n结果: {passed}/{len(OPEN_TITAN_RTL)} 通过")
    return passed >= len(OPEN_TITAN_RTL) - 1


if __name__ == '__main__':
    main()
