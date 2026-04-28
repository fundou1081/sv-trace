#!/usr/bin/env python3
"""
开源项目追踪测试 - sv_trace
使用真实开源 RISC-V 项目测试信号追踪功能
"""
import sys
import os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.driver import DriverTracer
from trace.connection import ConnectionTracer


# 可用的开源项目
OPEN_SOURCE_PROJECTS = [
    ('picorv32', '/Users/fundou/my_dv_proj/picorv32/picorv32.v'),
    ('serv', '/Users/fundou/my_dv_proj/serv/rtl/serv_top.v'),
    ('basic_verilog', '/Users/fundou/my_dv_proj/basic_verilog/adder_tree.sv'),
]


def test_project_parse(project_name, filepath):
    """测试项目解析"""
    if not os.path.exists(filepath):
        print(f"  ⚠️  {project_name}: 文件不存在")
        return False
    
    try:
        parser = SVParser()
        parser.parse_file(filepath)
        return True
    except Exception as e:
        print(f"  ❌ {project_name}: 解析失败 - {e}")
        return False


def test_project_driver(project_name, filepath):
    """测试驱动追踪"""
    if not os.path.exists(filepath):
        return False
    
    try:
        parser = SVParser()
        parser.parse_file(filepath)
        
        drv = DriverTracer(parser)
        drivers = drv.get_drivers('*')
        
        print(f"    驱动数: {len(drivers)}")
        return len(drivers) > 0
    except Exception as e:
        print(f"    ❌ 驱动追踪失败: {e}")
        return False


def test_project_connection(project_name, filepath):
    """测试连接追踪"""
    if not os.path.exists(filepath):
        return False
    
    try:
        parser = SVParser()
        parser.parse_file(filepath)
        
        tracer = ConnectionTracer(parser)
        instances = tracer.get_all_instances()
        
        print(f"    实例数: {len(instances)}")
        return True
    except Exception as e:
        print(f"    ⚠️  连接追踪: {e}")
        return False


def main():
    print("============================================================")
    print("开源项目 sv_trace 测试")
    print("============================================================")
    
    passed = 0
    total = 0
    
    for project_name, filepath in OPEN_SOURCE_PROJECTS:
        total += 1
        print(f"\n--- {project_name} ---")
        
        ok = test_project_parse(project_name, filepath)
        if ok:
            print(f"  ✅ 解析成功")
            
            # 测试驱动追踪
            test_project_driver(project_name, filepath)
            
            # 测试连接追踪  
            test_project_connection(project_name, filepath)
            
            passed += 1
        else:
            print(f"  ❌ 解析失败")
    
    print("\n============================================================")
    print(f"结果: {passed}/{total} 项目通过")
    print("============================================================")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
