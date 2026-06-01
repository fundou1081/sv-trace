#!/usr/bin/env python3
"""
OpenTitan 项目 sv_verify 详细测试
测试验证工具: FSM, 依赖分析, 代码质量
"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.driver import DriverTracer
from debug.fsm import FSMExtractor
from debug.dependency import ModuleDependencyAnalyzer


# 更多 OpenTitan 模块
OPEN_TITAN_MODULES = [
    '/Users/fundou/my_dv_proj/opentitan/hw/ip/uart/rtl/uart_core.sv',
    '/Users/fundou/my_dv_proj/opentitan/hw/ip/gpio/rtl/gpio.sv',
    '/Users/fundou/my_dv_proj/opentitan/hw/ip/spi_host/rtl/spi_host.sv',
    '/Users/fundou/my_dv_proj/opentitan/hw/ip/edn/rtl/edn_core.sv',
]


def test_fsm_extraction(parser, name):
    """测试 FSM 提取"""
    try:
        extractor = FSMExtractor(parser)
        fsms = extractor.find_all_fsm()
        return len(fsms)
    except:
        return 0


def test_module_dependency(parser, name):
    """测试模块依赖分析"""
    try:
        analyzer = ModuleDependencyAnalyzer(parser)
        modules = analyzer.get_all_modules()
        return len(modules)
    except:
        return 0


def test_code_complexity(parser, name):
    """测试代码复杂度分析"""
    try:
        drv = DriverTracer(parser)
        drivers = drv.get_drivers('*')
        
        # 简单计算复杂度指标
        total_drivers = len(drivers)
        complexity = min(10, total_drivers // 10)
        
        return complexity
    except:
        return 0


def test_reset_domain(parser, name):
    """测试复位域识别"""
    try:
        # 检查是否有复位逻辑
        drv = DriverTracer(parser)
        drivers = drv.get_drivers('*')
        
        # 查找包含 rst 的信号
        rst_signals = [d.signal for d in drivers if 'rst' in d.signal.lower() or 'reset' in d.signal.lower()]
        
        return len(rst_signals)
    except:
        return 0


def main():
    print("=" * 60)
    print("OpenTitan sv_verify 详细测试")
    print("=" * 60)
    
    results = {
        'FSM': [],
        '模块依赖': [],
        '复杂度': [],
        '复位域': [],
    }
    
    for filepath in OPEN_TITAN_MODULES:
        if not os.path.exists(filepath):
            continue
            
        name = os.path.basename(os.path.dirname(filepath))
        print(f"\n--- {name} ---")
        
        try:
            parser = SVParser()
            parser.parse_file(filepath)
            
            # FSM 提取
            fsm_count = test_fsm_extraction(parser, name)
            print(f"  FSM: {fsm_count}")
            results['FSM'].append(fsm_count)
            
            # 模块依赖
            dep_count = test_module_dependency(parser, name)
            print(f"  模块依赖: {dep_count}")
            results['模块依赖'].append(dep_count)
            
            # 代码复杂度
            complexity = test_code_complexity(parser, name)
            print(f"  复杂度: {complexity}/10")
            results['复杂度'].append(complexity)
            
            # 复位域
            rst_count = test_reset_domain(parser, name)
            print(f"  复位域: {rst_count}")
            results['复位域'].append(rst_count)
            
        except Exception as e:
            print(f"  ❌ 错误: {str(e)[:30]}")
    
    print("\n" + "=" * 60)
    print("汇总统计:")
    for key, vals in results.items():
        avg = sum(vals) / len(vals) if vals else 0
        print(f"  {key}: 平均 {avg:.1f}")
    print("=" * 60)


if __name__ == '__main__':
    main()
