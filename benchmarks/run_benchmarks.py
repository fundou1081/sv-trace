#!/usr/bin/env python3
"""运行 Driver/Load 基准测试

测试各个覆盖不同场景的 SystemVerilog 文件
"""

import sys
import os
import glob

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.query import SignalChainQuery


BENCHMARK_DIR = '/Users/fundou/my_dv_proj/sv-trace/benchmarks'


# 金标准定义 (人工推导)
BENCHMARKS = {
    '01_basic_registers': {
        'signals': ['data_out'],
        'expected': {
            'data_out': {
                'type': 'always_ff',
                'drivers_min': 1,
                'sources': ['data_in'],
                'clock': 'clk',
                'reset': 'rst_n'
            }
        }
    },
    '02_combinational': {
        'signals': ['result1', 'result2'],
        'expected': {
            'result1': {'type': 'always_comb', 'drivers_min': 1},
            'result2': {'type': 'continuous', 'drivers_min': 1, 'sources': ['a', 'b']}
        }
    },
    '03_bit_operations': {
        'signals': ['high_byte', 'low_byte', 'byte_swap'],
        'expected': {
            'high_byte': {'type': 'continuous', 'drivers_min': 1, 'sources': ['data_in']},
            'low_byte': {'type': 'continuous', 'drivers_min': 1, 'sources': ['data_in']},
            'byte_swap': {'type': 'continuous', 'drivers_min': 1}
        }
    },
    '04_generate_for': {
        'signals': ['pipeline_q'],
        'expected': {
            'pipeline_q': {'type': 'always_ff', 'drivers_min': 4}
        }
    },
    '05_priority_encoder': {
        'signals': ['grant', 'valid'],
        'expected': {
            'grant': {'type': 'always_comb', 'drivers_min': 1},
            'valid': {'type': 'always_comb', 'drivers_min': 1}
        }
    },
    '06_case_decoding': {
        'signals': ['is_load', 'is_store', 'is_branch', 'is_arith'],
        'expected': {
            'is_load': {'type': 'always_comb', 'drivers_min': 1}
        }
    },
    '07_fsm': {
        'signals': ['state_out', 'busy'],
        'expected': {
            'state_out': {'type': 'always_ff', 'drivers_min': 1},
            'busy': {'type': 'always_comb', 'drivers_min': 1}
        }
    },
    '08_complex_fsm': {
        'signals': ['result', 'done'],
        'expected': {
            'result': {'type': 'always_ff', 'drivers_min': 1},
            'done': {'type': 'always_comb', 'drivers_min': 1}
        }
    },
    '09_reset_strategies': {
        'signals': ['sync_out', 'async_out', 'multi_rst_out'],
        'expected': {
            'sync_out': {'type': 'always_ff', 'drivers_min': 1},
            'async_out': {'type': 'always_ff', 'drivers_min': 1}
        }
    },
    '10_pipeline': {
        'signals': ['data_out', 'valid_out'],
        'expected': {
            'data_out': {'type': 'always_ff', 'drivers_min': 1},
            'valid_out': {'type': 'always_ff', 'drivers_min': 1}
        }
    }
}


def test_benchmark(name, filepath):
    """测试单个基准文件"""
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"{'='*60}")
    
    # 解析
    parser = SVParser()
    tree = parser.parse_file(filepath)
    
    # parse_file 返回 SyntaxTree 或 None，但数据在 parser.trees 中
    if not parser.trees:
        print(f"❌ 解析失败")
        return False
    
    query = SignalChainQuery(parser)
    signals_found = len(query._signal_modules)
    print(f"发现信号: {signals_found}")
    
    # 获取基准定义
    spec = BENCHMARKS.get(name, {})
    test_signals = spec.get('signals', [])
    
    passed = 0
    failed = 0
    
    for sig in test_signals:
        if sig not in query._signal_modules:
            print(f"  ⚠️ {sig}: 未找到")
            failed += 1
            continue
        
        result = query.trace(sig, None)
        drivers = len(result.data.drivers) if result.data else 0
        loads = len(result.data.loads) if result.data else 0
        
        # 获取驱动类型
        kinds = set()
        sources = set()
        if result.data:
            for d in result.data.drivers:
                kinds.add(d.kind.lower())
                sources.update(d.sources)
        
        print(f"  ✅ {sig}: drivers={drivers} loads={loads} types={kinds}")
        
        # 简单验证
        if drivers > 0:
            passed += 1
        else:
            failed += 1
    
    print(f"结果: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """主函数"""
    print("=" * 60)
    print("Driver/Load 基准测试")
    print("=" * 60)
    
    # 查找所有基准文件
    pattern = os.path.join(BENCHMARK_DIR, '*.sv')
    files = glob.glob(pattern)
    
    if not files:
        print(f"❌ 未找到基准文件: {pattern}")
        sys.exit(1)
    
    print(f"找到 {len(files)} 个基准文件")
    
    # 运行测试
    results = {}
    for filepath in sorted(files):
        name = os.path.basename(filepath).replace('.sv', '')
        try:
            ok = test_benchmark(name, filepath)
            results[name] = 'PASS' if ok else 'FAIL'
        except Exception as e:
            print(f"❌ {name}: 错误 - {e}")
            results[name] = 'ERROR'
    
    # 汇总
    print("\n" + "=" * 60)
    print("汇总")
    print("=" * 60)
    for name, status in sorted(results.items()):
        print(f"  {name}: {status}")
    
    passed = sum(1 for s in results.values() if s == 'PASS')
    print(f"\n总计: {passed}/{len(results)} 通过")


if __name__ == '__main__':
    main()
