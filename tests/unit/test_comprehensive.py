"""
综合测试 - 运行所有测试用例
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parse import SVParser
from trace.driver import DriverCollector
from trace.load import LoadTracer, LoadTracerRegex
from trace.dependency import DependencyAnalyzer, FanoutAnalyzer
from trace.dataflow import DataFlowTracer
from trace.controlflow import ControlFlowTracer
from trace.connection import ConnectionTracer


TARGETED_DIR = os.path.join(os.path.dirname(__file__), '..', 'targeted')


def test_file(filename, analyzers):
    """测试单个文件"""
    filepath = os.path.join(TARGETED_DIR, filename)
    if not os.path.exists(filepath):
        return {"status": "skip", "reason": "file not found"}
    
    try:
        parser = SVParser()
        parser.parse_file(filepath)
        
        results = {}
        for name, analyzer_class in analyzers:
            try:
                analyzer = analyzer_class(parser)
                if hasattr(analyzer, 'find_high_fanout_signals'):
                    result = len(analyzer.find_high_fanout_signals(threshold=2))
                elif hasattr(analyzer, 'get_all_signals'):
                    result = len(analyzer.get_all_signals())
                elif hasattr(analyzer, 'find_flow'):
                    result = analyzer.find_flow('clk') or 0
                elif hasattr(analyzer, 'get_signal_connections'):
                    result = len(analyzer.get_signal_connections('clk') or [])
                elif hasattr(analyzer, 'get_connections'):
                    result = len(analyzer.get_connections())
                else:
                    result = "ok"
                results[name] = {"status": "ok", "result": result}
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)[:50]}
        
        return {"status": "ok", "results": results}
    except Exception as e:
        return {"status": "error", "error": str(e)[:50]}


def run_all_tests():
    """运行所有测试"""
    print("="*70)
    print("SV-Trace 综合测试")
    print("="*70)
    
    # 测试文件列表
    test_files = [
        # 针对性测试
        ("FSM Targeted", "test_fsm_targeted.sv", [
            ("Driver", DriverCollector),
            ("Fanout", FanoutAnalyzer),
            ("DataFlow", DataFlowTracer),
        ]),
        ("CDC Targeted", "test_cdc_targeted.sv", [
            ("Driver", DriverCollector),
            ("Fanout", FanoutAnalyzer),
        ]),
        ("Condition Targeted", "test_condition_targeted.sv", [
            ("Driver", DriverCollector),
            ("LoadTracer", LoadTracer),
        ]),
        ("Fanout Targeted", "test_fanout_targeted.sv", [
            ("Driver", DriverCollector),
            ("Fanout", FanoutAnalyzer),
        ]),
        ("Reset Targeted", "test_reset_targeted.sv", [
            ("Driver", DriverCollector),
            ("LoadTracer", LoadTracerRegex),
        ]),
        # Corner Cases
        ("FSM Corners", "test_fsm_corners.sv", [
            ("Driver", DriverCollector),
            ("Fanout", FanoutAnalyzer),
        ]),
        ("CDC Corners", "test_cdc_corners.sv", [
            ("Driver", DriverCollector),
            ("Fanout", FanoutAnalyzer),
        ]),
        ("Condition Corners", "test_condition_corners.sv", [
            ("Driver", DriverCollector),
            ("LoadTracer", LoadTracer),
        ]),
        ("Fanout Reset Corners", "test_fanout_reset_corners.sv", [
            ("Driver", DriverCollector),
            ("Fanout", FanoutAnalyzer),
            ("DataFlow", DataFlowTracer),
        ]),
        # OpenTitan Style
        ("OpenTitan Style", "test_opentitan_style.sv", [
            ("Driver", DriverCollector),
            ("Fanout", FanoutAnalyzer),
            ("Connection", ConnectionTracer),
        ]),
        # Verification Patterns
        ("Verification Patterns", "test_verification_patterns.sv", [
            ("Driver", DriverCollector),
            ("ControlFlow", ControlFlowTracer),
        ]),
        # Advanced Edge Cases
        ("Advanced Edge Cases", "test_edge_cases_advanced.sv", [
            ("Driver", DriverCollector),
            ("Fanout", FanoutAnalyzer),
            ("DataFlow", DataFlowTracer),
            ("ControlFlow", ControlFlowTracer),
        ]),
        # Foundation Tests
        ("LoadTracer Foundation", "test_load_tracer_foundation.sv", [
            ("Driver", DriverCollector),
            ("LoadTracer", LoadTracerRegex),
            ("Fanout", FanoutAnalyzer),
        ]),
        ("Cross Module", "test_cross_module.sv", [
            ("Driver", DriverCollector),
            ("Connection", ConnectionTracer),
        ]),
        ("Circular Dependency", "test_circular_dependency.sv", [
            ("Driver", DriverCollector),
            ("Dependency", DependencyAnalyzer),
        ]),
        ("Boundary Conditions", "test_boundary_conditions.sv", [
            ("Driver", DriverCollector),
            ("Fanout", FanoutAnalyzer),
        ]),
    ]
    
    results = {}
    total_pass = 0
    total_fail = 0
    
    for name, filename, analyzers in test_files:
        print(f"\n--- {name} ---")
        result = test_file(filename, analyzers)
        
        if result["status"] == "skip":
            print(f"  ⏭️  Skipped: {result.get('reason', '')}")
            continue
        
        if result["status"] == "error":
            print(f"  ❌ Error: {result.get('error', '')}")
            total_fail += 1
            results[name] = "FAIL"
            continue
        
        file_ok = True
        for an_name, an_result in result.get("results", {}).items():
            if an_result["status"] == "ok":
                print(f"  ✅ {an_name}: {an_result.get('result', 'ok')}")
            else:
                print(f"  ❌ {an_name}: {an_result.get('error', '')}")
                file_ok = False
        
        if file_ok:
            print(f"  ✅ PASS")
            total_pass += 1
            results[name] = "PASS"
        else:
            print(f"  ❌ FAIL")
            total_fail += 1
            results[name] = "FAIL"
    
    # Summary
    print("\n" + "="*70)
    print("测试汇总")
    print("="*70)
    
    for name, status in results.items():
        symbol = "✅" if status == "PASS" else "❌"
        print(f"  {symbol} {name}: {status}")
    
    print(f"\n总计: {total_pass}/{total_pass + total_fail} 通过")
    
    if total_fail == 0:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️  {total_fail} 个测试失败")
    
    return total_fail == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
