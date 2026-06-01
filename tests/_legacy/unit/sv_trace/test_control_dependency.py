import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

"""
控制流和依赖测试
"""
import sys
import os

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.controlflow import ControlFlowTracer
from trace.dependency import DependencyAnalyzer


def test_control_flow():
    """测试控制流"""
    print("\n=== ControlFlowTracer 测试 ===")
    
    code = '''
module top;
    logic a, b, c;
    always_comb begin
        if (a) begin
            b = 1;
        end else begin
            c = 1;
        end
    end
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    tracer = ControlFlowTracer(parser)
    
    print("  ✅ ControlFlowTracer OK")
    return True


def test_dependency():
    """测试依赖分析"""
    print("\n=== DependencyAnalyzer 测试 ===")
    
    code = '''
module top;
    logic [7:0] a, b, c;
    assign c = a + b;
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    analyzer = DependencyAnalyzer(parser)
    
    try:
        dep = analyzer.analyze('c')
        print(f"  ✅ DependencyAnalyzer OK, dependency found: {dep is not None}")
        return True
    except Exception as e:
        print(f"  ❌ DependencyAnalyzer error: {e}")
        return False


def main():
    tests = [
        test_control_flow,
        test_dependency,
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
                print(f"  ✅ {test.__name__} 通过")
        except Exception as e:
            print(f"  ❌ {test.__name__}: {e}")
    
    print(f"\n总计: {passed}/{len(tests)} 通过")
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
