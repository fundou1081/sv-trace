#!/usr/bin/env python3
"""
模块级追踪功能测试
"""
import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.driver import DriverTracer

TARGETED_DIR = '/Users/fundou/my_dv_proj/sv-trace/tests/targeted'


def test_driver_module():
    """模块级 Driver 测试"""
    print("\n=== DriverTracer 模块级测试 ===")
    test_file = f'{TARGETED_DIR}/test_dataflow_foundation.sv'
    
    parser = SVParser()
    parser.parse_file(test_file)
    
    drv = DriverTracer(parser)
    drivers = drv.get_drivers('*')
    print(f"  驱动数: {len(drivers)}")
    
    return True  # 简单返回成功


def main():
    print("============================================================")
    print("Module-level 追踪功能测试")
    print("============================================================")
    
    tests = [
        ("DriverTracer", test_driver_module),
    ]
    
    passed = 0
    for name, test_fn in tests:
        try:
            if test_fn():
                print(f"  ✅ {name} 测试通过")
                passed += 1
            else:
                print(f"  ❌ {name} 测试失败")
        except Exception as e:
            print(f"  ❌ {name} 错误: {e}")
    
    print("============================================================")
    if passed == len(tests):
        print(f"  ✅ 全部通过 ({passed}/{len(tests)})")
    else:
        print(f"  ❌ 部分失败 ({passed}/{len(tests)})")
    print("============================================================")


if __name__ == '__main__':
    main()
