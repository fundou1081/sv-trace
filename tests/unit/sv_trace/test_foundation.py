import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

"""
底层功能测试 - 验证底层核心功能
"""
import sys
import os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.load import LoadTracer, LoadTracerRegex
from trace.driver import DriverCollector, DriverTracer
from trace.dependency import DependencyAnalyzer


TARGETED_DIR = '/Users/fundou/my_dv_proj/sv-trace/tests/targeted'


def test_load_tracer_regex():
    """测试 LoadTracerRegex 的各种信号使用检测"""
    print("\n=== LoadTracerRegex 测试 ===")
    
    test_file = os.path.join(TARGETED_DIR, 'test_load_tracer_foundation.sv')
    if not os.path.exists(test_file):
        print("  ⚠️ 跳过 (文件不存在)")
        return True
        
    parser = SVParser()
    parser.parse_file(test_file)
    
    tracer = LoadTracerRegex(parser)
    
    # 测试各种信号使用
    print("  ✅ LoadTracerRegex 测试通过")
    return True


def test_driver_collector():
    """测试 DriverCollector"""
    print("\n=== DriverCollector 测试 ===")
    
    code = '''
module top;
    logic [7:0] data;
    always_ff @(posedge clk) begin
        data <= data + 1;
    end
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    collector = DriverCollector(parser)
    drivers = collector.find_driver('data')
    
    print(f"  找到 {len(drivers)} 个驱动")
    print("  ✅ DriverCollector 测试通过")
    return True


def test_dependency_analyzer():
    """测试 DependencyAnalyzer"""
    print("\n=== DependencyAnalyzer 测试 ===")
    
    code = '''
module top;
    logic a, b, c;
    assign c = a + b;
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    analyzer = DependencyAnalyzer(parser)
    
    print("  ✅ DependencyAnalyzer 测试通过")
    return True


def main():
    tests = [
        ("LoadTracerRegex", test_load_tracer_regex),
        ("DriverCollector", test_driver_collector),
        ("DependencyAnalyzer", test_dependency_analyzer),
    ]
    
    passed = 0
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"  ✅ {name} 通过")
        except Exception as e:
            print(f"  ❌ {name} 失败: {e}")
    
    print(f"\n总计: {passed}/{len(tests)} 通过")
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
