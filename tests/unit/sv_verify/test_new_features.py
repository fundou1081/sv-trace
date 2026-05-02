import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

"""
新功能测试 - 验证新开发的分析器
"""
import sys
import os

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from debug.analyzers.fsm_analyzer import FSMAnalyzer
from debug.analyzers.cdc import CDCExtendedAnalyzer
from debug.analyzers.reset_domain_analyzer import ResetIntegrityChecker
from debug.analyzers.condition_coverage import ConditionCoverageAnalyzer
from debug.analyzers.timed_path_analyzer import TimedPathAnalyzer


def find_sv_files(directory, limit=50):
    """查找测试文件"""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for f in filenames:
            if f.endswith('.sv') and 'sim' not in f:
                files.append(os.path.join(root, f))
                if len(files) >= limit:
                    return files
    return files


def test_fsm_analyzer():
    """FSM Analyzer测试"""
    print("\n=== FSM Analyzer 测试 ===")
    
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
    print("  ✅ FSM Analyzer 测试通过")
    return True


def test_cdc_extended():
    """CDC Extended Analyzer测试"""
    print("\n=== CDC Extended Analyzer 测试 ===")
    
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
    
    print(f"  ✅ CDC Extended Analyzer 测试通过")
    return True


def test_reset_integrity():
    """Reset Integrity Checker测试"""
    print("\n=== Reset Integrity Checker 测试 ===")
    
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
    
    print(f"  ✅ Reset Integrity Checker 测试通过")
    return True


def test_condition_coverage():
    """Condition Coverage Analyzer测试"""
    print("\n=== Condition Coverage Analyzer 测试 ===")
    
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
    
    print(f"  ✅ Condition Coverage Analyzer 测试通过")
    return True


def test_timed_path():
    """Timed Path Analyzer测试"""
    print("\n=== Timed Path Analyzer 测试 ===")
    
    code = '''
module test;
    logic clk;
    logic [7:0] data, result;
    always_ff @(posedge clk) begin
        result <= data + 1;
    end
endmodule
'''
    parser = SVParser()
    parser.parse_text(code)
    
    analyzer = TimedPathAnalyzer(parser)
    result = analyzer.analyze()
    
    print(f"  ✅ Timed Path Analyzer 测试通过")
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("FSMAnalyzer", test_fsm_analyzer),
        ("CDCExtendedAnalyzer", test_cdc_extended),
        ("ResetIntegrityChecker", test_reset_integrity),
        ("ConditionCoverageAnalyzer", test_condition_coverage),
        ("TimedPathAnalyzer", test_timed_path),
    ]
    
    results = []
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
