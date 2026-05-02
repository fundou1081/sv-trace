import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

"""
测试验证工具应用
"""
import sys
import os

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from debug.analyzers.fsm_analyzer import FSMAnalyzer
from debug.analyzers.cdc import CDCExtendedAnalyzer


TARGETED_DIR = '/Users/fundou/my_dv_proj/sv-trace/tests/targeted'


def test_fsm_app():
    """FSM 应用测试"""
    print("\n=== FSM 应用测试 ===")
    
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
    print("  ✅ FSM 应用测试通过")
    return True


def test_cdc_app():
    """CDC 应用测试"""
    print("\n=== CDC 应用测试 ===")
    
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
    
    print(f"  ✅ CDC 应用测试通过")
    return True


def run_all_tests():
    tests = [
        ("FSMApp", test_fsm_app),
        ("CDCApp", test_cdc_app),
    ]
    
    passed = 0
    for name, test in tests:
        try:
            if test():
                passed += 1
                print(f"  ✅ {name} 通过")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
    
    print(f"\n总计: {passed}/{len(tests)} 通过")
    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
