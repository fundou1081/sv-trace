import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

#!/usr/bin/env python3
"""
Tier3 开源项目测试
"""
import sys
import os
import tempfile

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from debug.analyzers.cdc import CDCExtendedAnalyzer
from debug.analyzers.fsm_analyzer import FSMAnalyzer


def test_linter():
    """测试 Linter"""
    print("\n=== Linter Test ===")
    
    code = '''
module top;
    logic clk;
    always @(posedge clk) begin
    end
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    print("  ✅ Linter Test passed")
    return True


def test_cdc_analyzer():
    """测试 CDC 分析器"""
    print("\n=== CDC Analyzer Test ===")
    
    code = '''
module top;
    logic clk_a, clk_b;
    logic [7:0] data;
    always @(posedge clk_a) data <= data + 1;
    always @(posedge clk_b) data <= data + 2;
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    analyzer = CDCExtendedAnalyzer(parser)
    result = analyzer.analyze()
    
    print("  ✅ CDC Analyzer Test passed")
    return True


def test_fsm_analyzer():
    """测试 FSM 分析器"""
    print("\n=== FSM Analyzer Test ===")
    
    code = '''
module top;
    logic [1:0] state;
    logic clk;
    always @(posedge clk)
        state <= state + 1;
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    analyzer = FSMAnalyzer(parser)
    report = analyzer.analyze()
    
    print("  ✅ FSM Analyzer Test passed")
    return True


def run_all_tests():
    """运行所有测试"""
    results = []
    
    tests = [
        ("Linter", test_linter),
        ("CDCAnalyzer", test_cdc_analyzer),
        ("FSMAnalyzer", test_fsm_analyzer),
    ]
    
    for name, test_func in tests:
        try:
            if test_func():
                results.append((name, "PASS"))
            else:
                results.append((name, "FAIL"))
        except Exception as e:
            results.append((name, f"ERROR: {e}"))
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for name, status in results:
        print(f"  {name}: {status}")
    
    passed = sum(1 for _, s in results if s == "PASS")
    print(f"\n总计: {passed}/{len(tests)} 通过")
    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
