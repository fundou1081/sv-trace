import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

"""
依赖分析测试
"""
import sys
import os

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.dependency import DependencyAnalyzer
from debug.dependency.analyzer import ModuleDependencyAnalyzer


def test_dependency_analyzer():
    """测试 DependencyAnalyzer"""
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
        print(f"  ✅ DependencyAnalyzer OK")
        return True
    except Exception as e:
        print(f"  ❌ DependencyAnalyzer error: {e}")
        return False


def test_module_dependency_analyzer():
    """测试 ModuleDependencyAnalyzer"""
    print("\n=== ModuleDependencyAnalyzer 测试 ===")
    
    code = '''
module top;
    logic clk;
    sub u_sub (.clk(clk));
endmodule

module sub(input clk);
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    try:
        analyzer = ModuleDependencyAnalyzer(parser)
        modules = analyzer.get_all_modules()
        print(f"  ✅ ModuleDependencyAnalyzer OK, found {len(modules)} modules")
        return True
    except Exception as e:
        print(f"  ❌ ModuleDependencyAnalyzer error: {e}")
        return False


def main():
    tests = [
        test_dependency_analyzer,
        test_module_dependency_analyzer,
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {e}")
    
    print(f"\n总计: {passed}/{len(tests)} 通过")
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
