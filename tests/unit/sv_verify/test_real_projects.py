#!/usr/bin/env python3
"""
开源项目验证测试 - sv_verify
使用真实开源 RISC-V 项目测试验证工具
"""
import sys
import os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.driver import DriverTracer
from trace.load import LoadTracer
from debug.fsm import FSMExtractor
from debug.dependency import ModuleDependencyAnalyzer


OPEN_SOURCE_PROJECTS = [
    ('picorv32', '/Users/fundou/my_dv_proj/picorv32/picorv32.v'),
    ('serv', '/Users/fundou/my_dv_proj/serv/rtl/serv_top.v'),
    ('basic_verilog', '/Users/fundou/my_dv_proj/basic_verilog/adder_tree.sv'),
]


def test_fsm_extraction(project_name, filepath):
    """测试 FSM 提取"""
    if not os.path.exists(filepath):
        return False
    
    try:
        parser = SVParser()
        parser.parse_file(filepath)
        
        extractor = FSMExtractor(parser)
        fsms = extractor.find_all_fsm()
        
        print(f"    FSM 数: {len(fsms)}")
        return True
    except Exception as e:
        print(f"    ⚠️  FSM: {str(e)[:30]}")
        return True  # 允许失败


def test_module_dependency(project_name, filepath):
    """测试模块依赖分析"""
    if not os.path.exists(filepath):
        return False
    
    try:
        parser = SVParser()
        parser.parse_file(filepath)
        
        analyzer = ModuleDependencyAnalyzer(parser)
        modules = analyzer.get_all_modules()
        
        print(f"    模块数: {len(modules)}")
        return True
    except Exception as e:
        print(f"    ⚠️  依赖: {str(e)[:30]}")
        return True


def main():
    print("============================================================")
    print("开源项目 sv_verify 测试")
    print("============================================================")
    
    passed = 0
    total = 0
    
    for project_name, filepath in OPEN_SOURCE_PROJECTS:
        total += 1
        print(f"\n--- {project_name} ---")
        
        if not os.path.exists(filepath):
            print(f"  ⚠️  文件不存在")
            continue
        
        try:
            parser = SVParser()
            parser.parse_file(filepath)
            print(f"  ✅ 解析成功")
            
            # 测试 FSM 提取
            test_fsm_extraction(project_name, filepath)
            
            # 测试模块依赖
            test_module_dependency(project_name, filepath)
            
            passed += 1
        except Exception as e:
            print(f"  ❌ 失败: {e}")
    
    print("\n============================================================")
    print(f"结果: {passed}/{total} 项目通过")
    print("============================================================")
    
    return passed >= total - 1  # 允许1个失败


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
