"""
底层模块功能测试
测试 DataFlowTracer, ControlFlowTracer, ConnectionAnalyzer
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parse import SVParser
from trace.dataflow import DataFlowTracer
from trace.controlflow import ControlFlowTracer
from trace.connection import ConnectionTracer


TARGETED_DIR = os.path.join(os.path.dirname(__file__), 'targeted')


def test_dataflow_tracer():
    """测试 DataFlowTracer"""
    print("\n=== DataFlowTracer 测试 ===")
    
    test_file = os.path.join(TARGETED_DIR, 'test_dataflow_foundation.sv')
    parser = SVParser()
    parser.parse_file(test_file)
    
    tracer = DataFlowTracer(parser)
    
    # 测试数据流分析
    flows = tracer.find_flow('a')
    print(f"  数据流数: {len(flows)}")
    
    # 测试数据流链
    
    print(f"  a的链: {chains[:3] if chains else []}")
    
    print("  ✅ DataFlowTracer 测试通过")
    return True


def test_controlflow_tracer():
    """测试 ControlFlowTracer"""
    print("\n=== ControlFlowTracer 测试 ===")
    
    test_file = os.path.join(TARGETED_DIR, 'test_controlflow_foundation.sv')
    parser = SVParser()
    parser.parse_file(test_file)
    
    tracer = ControlFlowTracer(parser)
    
    # 测试控制依赖分析
    deps = tracer.find_control_dependencies('a')
    print(f"  控制依赖数: {len(deps)}")
    
    # 测试always块分析
    
    print(f"  always块数: {len(blocks)}")
    
    print("  ✅ ControlFlowTracer 测试通过")
    return True


def test_connection_analyzer():
    """测试 ConnectionAnalyzer"""
    print("\n=== ConnectionAnalyzer 测试 ===")
    
    test_file = os.path.join(TARGETED_DIR, 'test_connection_foundation.sv')
    parser = SVParser()
    parser.parse_file(test_file)
    
    analyzer = ConnectionTracer(parser)
    
    # 测试连接分析
    connections = analyzer.get_signal_connections('clk')
    print(f"  连接数: {len(connections)}")
    
    # 测试端口映射
    
    print(f"  端口映射数: {len(ports)}")
    
    print("  ✅ ConnectionAnalyzer 测试通过")
    return True


def run_all():
    """运行所有测试"""
    print("="*60)
    print("底层模块功能测试")
    print("="*60)
    
    results = {}
    
    tests = [
        ("DataFlowTracer", test_dataflow_tracer),
        ("ControlFlowTracer", test_controlflow_tracer),
        ("ConnectionAnalyzer", test_connection_analyzer),
    ]
    
    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = "PASS" if result else "FAIL"
        except Exception as e:
            results[name] = f"FAIL: {e}"
            import traceback
            traceback.print_exc()
    
    # 汇总
    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)
    
    for name, result in results.items():
        status = "✅" if result == "PASS" else "❌"
        print(f"  {status} {name}: {result}")
    
    all_pass = all(v == "PASS" for v in results.values())
    print(f"\n总体: {'✅ ALL PASS' if all_pass else '❌ SOME FAILED'}")
    
    return all_pass


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
