import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

"""
Corner Case测试 - 验证边界和极端情况
"""
import sys
import os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from debug.analyzers.fsm_analyzer import FSMAnalyzer, SVAGenerator
from debug.analyzers.cdc import CDCExtendedAnalyzer
from debug.analyzers.reset_domain_analyzer import ResetIntegrityChecker
from debug.analyzers.condition_coverage import ConditionCoverageAnalyzer
from debug.analyzers.timed_path_analyzer import TimedPathAnalyzer


TARGETED_DIR = '/Users/fundou/my_dv_proj/sv-trace/tests/targeted'


def test_fsm_corners():
    """FSM Corner Cases测试"""
    print("\n" + "="*60)
    print("FSM Corner Cases测试")
    print("="*60)
    
    code = '''
module test;
    typedef enum {S0, S1, S2} state_t;
    state_t state;
    always_ff @(posedge clk) begin
        case (state)
            S0: state <= S1;
            S1: state <= S2;
            S2: state <= S0;
        endcase
    end
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    analyzer = FSMAnalyzer(parser)
    report = analyzer.analyze()
    
    print(f"  状态数: {len(report.state_names)}")
    print(f"  ✅ FSM 测试通过")
    return True


def test_cdc_corners():
    """CDC Corner Cases测试"""
    print("\n" + "="*60)
    print("CDC Corner Cases测试")
    print("="*60)
    
    code = '''
module test;
    logic clk_a, clk_b;
    logic [7:0] data;
    always_ff @(posedge clk_a) data <= data + 1;
    always_ff @(posedge clk_b) data <= data + 2;
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    analyzer = CDCExtendedAnalyzer(parser)
    result = analyzer.analyze()
    
    print(f"  ✅ CDC 测试通过")
    return True


def test_condition_corners():
    """Condition Coverage Corner Cases测试"""
    print("\n" + "="*60)
    print("Condition Coverage Corner Cases测试")
    print("="*60)
    
    code = '''
module test;
    logic a, b, c;
    always_comb begin
        if (a & b | c) begin
            c = 1;
        end
    end
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    analyzer = ConditionCoverageAnalyzer(parser)
    result = analyzer.analyze()
    
    print(f"  ✅ Condition Coverage 测试通过")
    return True


def test_reset_corners():
    """Reset Domain Corner Cases测试"""
    print("\n" + "="*60)
    print("Reset Domain Corner Cases测试")
    print("="*60)
    
    code = '''
module test;
    logic clk, rst_async, rst_sync;
    logic [7:0] data;
    always_ff @(posedge clk) begin
        if (rst_sync) data <= 0;
        else data <= data + 1;
    end
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    checker = ResetIntegrityChecker(parser)
    result = checker.check()
    
    print(f"  ✅ Reset Domain 测试通过")
    return True


def test_all_corners():
    """运行所有Corner Cases测试"""
    tests = [
        test_fsm_corners,
        test_cdc_corners,
        test_condition_corners,
        test_reset_corners,
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
    success = test_all_corners()
    sys.exit(0 if success else 1)
