import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

"""
性能基准测试
"""
import sys
import os
import time

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.driver import DriverCollector
from trace.load import LoadTracer
from debug.analyzers.fsm_analyzer import FSMAnalyzer
from debug.analyzers.cdc import CDCExtendedAnalyzer


def benchmark_parser():
    """Parser 性能测试"""
    print("\n=== Parser 性能测试 ===")
    
    code = '''
module top;
    logic [7:0] data;
    logic clk;
    always_ff @(posedge clk) begin
        data <= data + 1;
    end
endmodule
'''
    
    times = []
    for _ in range(10):
        parser = SVParser()
        start = time.time()
        parser.parse_text(code)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    avg = sum(times) / len(times)
    print(f"  平均: {avg:.4f} ms")
    return True


def benchmark_driver():
    """DriverCollector 性能测试"""
    print("\n=== DriverCollector 性能测试 ===")
    
    code = '''
module top;
    logic [7:0] data;
    logic clk;
    always_ff @(posedge clk) begin
        data <= data + 1;
    end
endmodule
'''
    
    parser = SVParser()
    parser.parse_text(code)
    
    start = time.time()
    tracer = DriverCollector(parser)
    drivers = tracer.find_driver('data')
    elapsed = (time.time() - start) * 1000
    
    print(f"  耗时: {elapsed:.4f} ms")
    return True


def benchmark_load():
    """LoadTracer 性能测试"""
    print("\n=== LoadTracer 性能测试 ===")
    
    code = '''
module top;
    logic [7:0] data;
    logic clk;
    always_ff @(posedge clk) begin
        data <= data + 1;
    end
endmodule
'''
    
    parser = SVParser()
    parser.parse_text(code)
    
    start = time.time()
    tracer = LoadTracer(parser)
    loads = tracer.find_load('clk')
    elapsed = (time.time() - start) * 1000
    
    print(f"  耗时: {elapsed:.4f} ms")
    return True


def benchmark_fsm():
    """FSMAnalyzer 性能测试"""
    print("\n=== FSMAnalyzer 性能测试 ===")
    
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
    
    start = time.time()
    analyzer = FSMAnalyzer(parser)
    report = analyzer.analyze()
    elapsed = (time.time() - start) * 1000
    
    print(f"  耗时: {elapsed:.4f} ms")
    return True


def run_all_tests():
    tests = [
        ("Parser", benchmark_parser),
        ("DriverCollector", benchmark_driver),
        ("LoadTracer", benchmark_load),
        ("FSMAnalyzer", benchmark_fsm),
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
