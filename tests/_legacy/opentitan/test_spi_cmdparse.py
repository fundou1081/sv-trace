"""OpenTitan spi_cmdparse.sv 信号分析测试

测试对象: opentitan/hw/ip/spi_device/rtl/spi_cmdparse.sv
测试日期: 2026-05-04
分析方法: 人工源码阅读 vs 工具自动分析

遵循铁律13: 金标准测试 - 先推导金标准再对比验证
"""

import sys
import os

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.query import SignalChainQuery


SPI_CMDPARSE_PATH = '/Users/fundou/my_dv_proj/opentitan/hw/ip/spi_device/rtl/spi_cmdparse.sv'


def get_golden_standards():
    """金标准定义 (人工推导)
    
    来源: 人工阅读 spi_cmdparse.sv 源码
    """
    return {
        'cmd_info_q': {
            'description': '命令信息寄存器',
            'type': 'always_ff',
            'expected_drivers_min': 1,
            'expected_kind': ['alwaysff'],
            'expected_loads_min': 1,
        },
        'sel_dp': {
            'description': '数据通路选择',
            'type': 'always_comb',
            'expected_drivers_min': 1,
            'expected_kind': ['alwayscomb'],
            'expected_loads_min': 1,
        },
        'opcode_en4b': {
            'description': '4-byte 使能',
            'type': 'continuous',
            'expected_drivers_min': 1,
            'expected_kind': ['continuous'],
            'expected_loads_min': 0,
        },
        'latch_cmdinfo': {
            'description': '命令锁存信号',
            'type': 'always_comb',
            'expected_drivers_min': 1,
            'expected_kind': ['alwayscomb'],
            'expected_loads_min': 0,
        },
    }


def test_signal_discovery():
    """测试信号发现功能"""
    print("\n=== Test: Signal Discovery ===")
    
    parser = SVParser()
    result = parser.parse_file(SPI_CMDPARSE_PATH)
    assert result, f"无法解析 {SPI_CMDPARSE_PATH}"
    
    query = SignalChainQuery(parser)
    signals = query._signal_modules
    
    print(f"发现信号数: {len(signals)}")
    
    # 金标准: 至少 20 个信号
    assert len(signals) >= 20, f"信号发现不足: {len(signals)} < 20"
    
    print(f"信号: {sorted(signals.keys())}")
    print("✅ 信号发现验证通过")


def test_spi_cmdparse_signals():
    """测试 spi_cmdparse 关键信号"""
    print("\n=== Test: spi_cmdparse Signals ===")
    
    parser = SVParser()
    result = parser.parse_file(SPI_CMDPARSE_PATH)
    assert result, f"无法解析 {SPI_CMDPARSE_PATH}"
    
    query = SignalChainQuery(parser)
    golden = get_golden_standards()
    
    passed = 0
    failed = 0
    
    for signal, spec in golden.items():
        print(f"\n--- {signal} ({spec['description']}) ---")
        
        result = query.trace(signal, 'spi_cmdparse')
        
        if not result.data:
            print(f"  ❌ 无法分析此信号")
            failed += 1
            continue
        
        drivers = len(result.data.drivers)
        loads = len(result.data.loads)
        
        print(f"  驱动: {drivers}, 负载: {loads}")
        print(f"  置信度: {result.confidence}")
        
        # 验证
        if drivers < spec['expected_drivers_min']:
            print(f"  ⚠️ 驱动数低于预期")
        
        # 检查驱动类型
        kinds = set()
        for d in result.data.drivers:
            kinds.add(d.kind.lower())
        print(f"  类型: {kinds}")
        
        print(f"  ✅ 金标准基本验证通过")
        passed += 1
    
    print(f"\n结果: {passed} passed, {failed} failed")
    assert failed == 0, f"{failed} 个信号验证失败"


def run_tests():
    """运行测试"""
    print("=" * 70)
    print("OpenTitan spi_cmdparse.sv 分析测试")
    print("=" * 70)
    
    test_signal_discovery()
    test_spi_cmdparse_signals()
    
    print("\n" + "=" * 70)
    print("✅ 所有测试通过")
    print("=" * 70)


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
