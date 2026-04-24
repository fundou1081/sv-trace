#!/usr/bin/env python3
"""
运行所有单元测试
"""
import sys
import os
import subprocess

# 确保可以导入 src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_tests():
    """运行 pytest"""
    test_dir = os.path.dirname(__file__)
    
    print("=" * 60)
    print("运行 sv-trace 单元测试")
    print("=" * 60)
    
    # 运行 pytest
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', test_dir, '-v', '--tb=short'],
        cwd=os.path.join(test_dir, '..')
    )
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(run_tests())
