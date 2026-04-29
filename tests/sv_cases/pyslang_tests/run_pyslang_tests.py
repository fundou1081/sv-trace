#!/usr/bin/env python3
"""
pyslang AST 针对性测试运行器
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))

from parse.class_utils import extract_classes_from_text
from parse.constraint import extract_constraints_from_text
from parse.module_io import ModuleIOExtractor
from debug.analyzers.clock_tree_analyzer import extract_clock_signals_from_text
from debug.analyzers.reset_domain_analyzer import extract_reset_signals_from_text

def test_class_file(filepath):
    """测试 class 文件"""
    print(f"\n{'='*60}")
    print(f"Class 测试: {os.path.basename(filepath)}")
    print('='*60)
    
    code = open(filepath).read()
    classes = extract_classes_from_text(code)
    constraints = extract_constraints_from_text(code)
    
    print(f"  Classes: {len(classes)}")
    print(f"  Constraints: {len(constraints)}")
    
    for c in classes[:5]:
        members = c.get('members', [])
        cons = c.get('constraints', [])
        print(f"    - {c['name']}: {len(members)} members, {len(cons)} constraints")
    
    return len(classes) > 0

def test_module_file(filepath):
    """测试 module IO 文件"""
    print(f"\n{'='*60}")
    print(f"Module IO 测试: {os.path.basename(filepath)}")
    print('='*60)
    
    code = open(filepath).read()
    ext = ModuleIOExtractor()
    modules = ext.extract_from_text(code)
    
    print(f"  Modules: {len(modules)}")
    for m in modules[:5]:
        print(f"    - {m.name}: {len(m.ports)} ports")
    
    return len(modules) > 0

def test_clock_file(filepath):
    """测试 clock 文件"""
    print(f"\n{'='*60}")
    print(f"Clock 测试: {os.path.basename(filepath)}")
    print('='*60)
    
    code = open(filepath).read()
    clocks = extract_clock_signals_from_text(code)
    
    print(f"  Clocks: {len(clocks)}")
    for c in clocks[:5]:
        print(f"    - {c['name']} ({c.get('edge', 'N/A')})")
    
    return len(clocks) > 0

def main():
    base_dir = os.path.dirname(__file__)
    
    print("="*60)
    print("pyslang AST 针对性测试")
    print("="*60)
    
    results = []
    
    # Class 测试
    if os.path.exists(os.path.join(base_dir, 'class_test.sv')):
        results.append(test_class_file(os.path.join(base_dir, 'class_test.sv')))
    
    # Module IO 测试
    if os.path.exists(os.path.join(base_dir, 'module_io_test.sv')):
        results.append(test_module_file(os.path.join(base_dir, 'module_io_test.sv')))
    
    # Clock/Reset 测试
    if os.path.exists(os.path.join(base_dir, 'clock_reset_test.sv')):
        results.append(test_clock_file(os.path.join(base_dir, 'clock_reset_test.sv')))
    
    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)
    passed = sum(results)
    print(f"  通过: {passed}/{len(results)}")
    
    return 0 if all(results) else 1

if __name__ == '__main__':
    sys.exit(main())
