"""
性能基准测试 - SV-Trace
测量核心功能的性能指标
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parse import SVParser
from trace.driver import DriverCollector
from trace.load import LoadTracer
from trace.dependency import FanoutAnalyzer, DependencyAnalyzer
from debug.analyzers.fsm_analyzer import FSMAnalyzer
from debug.analyzers.cdc import CDCExtendedAnalyzer

TARGETED_DIR = os.path.join(os.path.dirname(__file__), '..', 'targeted')


def measure_time(func, *args, **kwargs):
    """测量函数执行时间"""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    end = time.perf_counter()
    return result, (end - start) * 1000  # ms


def run_benchmark():
    """运行性能基准测试"""
    print("="*60)
    print("SV-Trace 性能基准测试")
    print("="*60)
    
    # 测试文件列表
    test_files = [
        'test_fsm_corners.sv',
        'test_cdc_corners.sv',
        'test_condition_corners.sv',
        'test_fanout_fixed.sv',
    ]
    
    results = []
    
    for fname in test_files:
        filepath = os.path.join(TARGETED_DIR, fname)
        if not os.path.exists(filepath):
            continue
        
        print(f"\n文件: {fname}")
        print("-"*40)
        
        # 1. Parse
        parser = SVParser()
        _, parse_time = measure_time(parser.parse_file, filepath)
        print(f"  解析: {parse_time:.2f} ms")
        
        # 2. DriverCollector
        dc = DriverCollector(parser)
        _, dc_time = measure_time(len, dc.get_all_signals())
        print(f"  DriverCollector: {dc_time:.4f} ms")
        
        # 3. LoadTracer
        lt = LoadTracer(parser)
        _, lt_time = measure_time(len, lt.get_all_signals())
        print(f"  LoadTracer: {lt_time:.4f} ms")
        
        # 4. FanoutAnalyzer
        fa = FanoutAnalyzer(parser)
        _, fa_time = measure_time(len, fa.find_high_fanout_signals(threshold=2))
        print(f"  FanoutAnalyzer: {fa_time:.4f} ms")
        
        # 5. FSMAnalyzer
        fsm = FSMAnalyzer(parser)
        _, fsm_time = measure_time(fsm.analyze)
        print(f"  FSMAnalyzer: {fsm_time:.2f} ms")
        
        # 6. CDCAnalyzer
        cdc = CDCExtendedAnalyzer(parser)
        _, cdc_time = measure_time(cdc.analyze)
        print(f"  CDCAnalyzer: {cdc_time:.2f} ms")
        
        total = parse_time + dc_time + lt_time + fa_time + fsm_time + cdc_time
        results.append({
            'file': fname,
            'parse': parse_time,
            'analyze': total - parse_time,
            'total': total
        })
    
    # 总结
    print("\n" + "="*60)
    print("性能汇总")
    print("="*60)
    
    avg_parse = sum(r['parse'] for r in results) / len(results)
    avg_analyze = sum(r['analyze'] for r in results) / len(results)
    
    print(f"平均解析时间: {avg_parse:.2f} ms")
    print(f"平均分析时间: {avg_analyze:.2f} ms")
    print(f"平均总时间: {avg_parse + avg_analyze:.2f} ms")
    
    # 性能评级
    if avg_analyze < 100:
        grade = "A - 优秀"
    elif avg_analyze < 500:
        grade = "B - 良好"
    elif avg_analyze < 1000:
        grade = "C - 一般"
    else:
        grade = "D - 需要优化"
    
    print(f"性能评级: {grade}")
    
    print("="*60)
    return results


if __name__ == '__main__':
    run_benchmark()
