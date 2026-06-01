#!/usr/bin/env python3
"""
sv-trace 测试运行器
运行所有测试用例并验证功能
"""
import sys
import os
import tempfile
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parse.parser import SVParser
from trace.driver import DriverTracer
from debug.fsm import FSMExtractor
from debug.dependency import ModuleDependencyAnalyzer
from debug.iospec import IOSpecExtractor


def test_driver():
    """测试 DriverTracer"""
    print("\n" + "=" * 60)
    print("DriverTracer 测试")
    print("=" * 60)
    
    test_file = os.path.join(os.path.dirname(__file__), 'sv_cases', 'driver', 'driver_basic.sv')
    parser = SVParser()
    parser.parse_file(test_file)
    
    tracer = DriverTracer(parser)
    
    tests = [
        ('driver_basic', ['a', 'b', 'c']),
        ('driver_always_ff', ['out']),
        ('driver_always_comb', ['c']),
        ('driver_if_else', ['out_data']),
        ('driver_case', ['out']),
    ]
    
    passed = 0
    for module_name, expected_signals in tests:
        signals = tracer.list_signals(module_name)
        if signals:
            print(f"  [{module_name}] OK - signals: {signals[:3]}...")
            passed += 1
        else:
            print(f"  [{module_name}] FAIL")
    
    print(f"\nDriverTracer: {passed}/{len(tests)} passed")
    return passed == len(tests)


def test_fsm():
    """测试 FSMExtractor"""
    print("\n" + "=" * 60)
    print("FSMExtractor 测试")
    print("=" * 60)
    
    test_file = os.path.join(os.path.dirname(__file__), 'sv_cases', 'fsm', 'fsm_simple.sv')
    parser = SVParser()
    parser.parse_file(test_file)
    
    extractor = FSMExtractor(parser)
    fsm_list = extractor.extract()
    
    print(f"  Found {len(fsm_list)} FSM(s)")
    
    for fsm in fsm_list:
        print(f"  - {fsm.name}: state_var={fsm.state_var}, states={len(fsm.states)}")
    
    return len(fsm_list) >= 1


def test_dependency():
    """测试 ModuleDependencyAnalyzer"""
    print("\n" + "=" * 60)
    print("ModuleDependencyAnalyzer 测试")
    print("=" * 60)
    
    test_file = os.path.join(os.path.dirname(__file__), 'sv_cases', 'dependency', 'dependency_hierarchy.sv')
    parser = SVParser()
    parser.parse_file(test_file)
    
    analyzer = ModuleDependencyAnalyzer(parser)
    graph = analyzer.analyze()
    
    print(f"  Modules: {len(graph.modules)}")
    print(f"  Root modules: {graph.root_modules}")
    
    # 检查是否找到 top 模块
    has_top = 'top' in graph.modules
    print(f"  Has 'top': {has_top}")
    
    if 'top' in graph.modules:
        top = graph.modules['top']
        print(f"  top depends_on: {top.depends_on}")
    
    return has_top and len(graph.modules) >= 3


def test_iospec():
    """测试 IOSpecExtractor"""
    print("\n" + "=" * 60)
    print("IOSpecExtractor 测试")
    print("=" * 60)
    
    test_file = os.path.join(os.path.dirname(__file__), 'sv_cases', 'iospec', 'iospec_basic.sv')
    parser = SVParser()
    parser.parse_file(test_file)
    
    extractor = IOSpecExtractor(parser)
    spec = extractor.extract('io_simple')
    
    print(f"  Module: {spec.module_name}")
    print(f"  Ports: {len(spec.ports)}")
    
    for p in spec.ports:
        print(f"    {p.direction.value:7} {p.name} -> {p.category.value}")
    
    return len(spec.ports) >= 5


def main():
    print("=" * 60)
    print("sv-trace 测试套件")
    print("=" * 60)
    
    results = []
    
    results.append(("DriverTracer", test_driver()))
    results.append(("FSMExtractor", test_fsm()))
    results.append(("ModuleDependency", test_dependency()))
    results.append(("IOSpecExtractor", test_iospec()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("所有测试通过!")
    else:
        print("部分测试失败")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
