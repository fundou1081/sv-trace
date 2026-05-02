import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

#!/usr/bin/env python3
"""
FSMAnalyzer 单元测试
"""
import sys
import os
import tempfile

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from debug.analyzers.fsm_analyzer import FSMAnalyzer


def test_simple_fsm():
    """测试简单状态机"""
    print("\n=== Simple FSM Test ===")
    
    code = """
module fsm(input clk, input rst_n);
    logic [1:0] state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= 2'b00;
        else state <= next_state;
    
    always_comb
        case (state)
            2'b00: next_state = 2'b01;
            2'b01: next_state = 2'b10;
            2'b10: next_state = 2'b00;
        endcase
endmodule
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        f.flush()
        
        parser = SVParser()
        parser.parse_file(f.name)
        
        analyzer = FSMAnalyzer(parser)
        report = analyzer.analyze()
        
        print(f"  States found: {len(report.state_names)}")
        print("  ✅ Simple FSM Test passed")
    
    os.unlink(f.name)
    return True


def test_fsm_with_enum():
    """测试 typedef enum 状态机"""
    print("\n=== FSM with Enum Test ===")
    
    code = """
module fsm(input clk, input rst_n);
    typedef enum logic [1:0] {IDLE, RUN, DONE} state_t;
    state_t state, next_state;
    
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) state <= IDLE;
        else state <= next_state;
    
    always_comb
        case (state)
            IDLE: next_state = RUN;
            RUN: next_state = DONE;
            DONE: next_state = IDLE;
        endcase
endmodule
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        f.flush()
        
        parser = SVParser()
        parser.parse_file(f.name)
        
        analyzer = FSMAnalyzer(parser)
        report = analyzer.analyze()
        
        print(f"  States found: {len(report.state_names)}")
        print("  ✅ FSM with Enum Test passed")
    
    os.unlink(f.name)
    return True


def main():
    tests = [
        test_simple_fsm,
        test_fsm_with_enum,
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
