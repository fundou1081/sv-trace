#!/usr/bin/env python3
"""
运行各子项目测试
"""
import os
import sys
import subprocess

SUBPROJECTS = ['sv_ast', 'sv_trace', 'sv_verify', 'sv_codecheck']

def run_tests(subproject):
    print(f"\n{'='*60}")
    print(f"运行 {subproject} 测试")
    print('='*60)
    
    test_dir = os.path.dirname(__file__)
    sub_dir = os.path.join(test_dir, subproject)
    
    # 查找测试文件
    test_files = [f for f in os.listdir(sub_dir) 
                  if f.startswith('test_') and f.endswith('.py')]
    
    os.chdir(test_dir)
    os.environ['PYTHONPATH'] = os.path.join(test_dir, '..', '..', 'src')
    
    passed = 0
    failed = 0
    
    for tf in test_files:
        if tf == '__init__.py':
            continue
        print(f"\n--- {tf} ---")
        result = subprocess.run(
            [sys.executable, tf],
            capture_output=True,
            text=True,
            env={**os.environ, 'PYTHONPATH': os.path.join(test_dir, '..', '..', 'src')}
        )
        if result.returncode == 0:
            passed += 1
            print("✅ PASS")
        else:
            failed += 1
            print("❌ FAIL")
            if result.stderr:
                print(result.stderr[:500])
    
    return passed, failed

def main():
    print("="*60)
    print("SV-Trace 子项目测试")
    print("="*60)
    
    total_passed = 0
    total_failed = 0
    
    for sub in SUBPROJECTS:
        p, f = run_tests(sub)
        total_passed += p
        total_failed += f
    
    print("\n" + "="*60)
    print(f"总计: {total_passed} 通过, {total_failed} 失败")
    print("="*60)

if __name__ == '__main__':
    main()
