#!/usr/bin/env python3
"""运行所有边界测试"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from tests.edge_cases.test_driver_edge import test_driver_edge_cases
from tests.edge_cases.test_load_edge import test_load_edge_cases
from tests.edge_cases.test_dependency_edge import test_dependency_edge_cases
from tests.edge_cases.test_debug_edge import test_debug_edge_cases
from tests.edge_cases.test_query_edge import test_query_edge_cases


def run_all():
    print("=" * 60)
    print("SV-TRACE 边界测试套件")
    print("=" * 60)
    
    all_results = {}
    
    # DriverCollector
    print("\n### DriverCollector ###")
    results = test_driver_edge_cases()
    all_results.update(results)
    for name, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {name}: {count}")
    
    # LoadTracer
    print("\n### LoadTracer ###")
    results = test_load_edge_cases()
    all_results.update(results)
    for name, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {name}: {count}")
    
    # DependencyAnalyzer
    print("\n### DependencyAnalyzer ###")
    results = test_dependency_edge_cases()
    all_results.update(results)
    for name, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {name}: {count}")
    
    # Debug Analyzers
    print("\n### Debug Analyzers ###")
    results = test_debug_edge_cases()
    all_results.update(results)
    for name, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {name}: {count}")
    
    # Query Modules
    print("\n### Query Modules ###")
    results = test_query_edge_cases()
    all_results.update(results)
    for name, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {name}: {count}")
    
    # Summary
    passed = sum(1 for c in all_results.values() if c > 0)
    total = len(all_results)
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} ({100*passed//total}%)")
    print("=" * 60)
    
    # 统计发现的 bugs
    bugs_found = total - passed
    print(f"\n发现 {bugs_found} 个潜在问题 (测试用例未通过)")


if __name__ == '__main__':
    run_all()
