"""
Corner Case测试 - 验证边界和极端情况
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parse import SVParser
from debug.analyzers.fsm_analyzer import FSMAnalyzer, SVAGenerator
from debug.analyzers.cdc import CDCExtendedAnalyzer
from debug.analyzers.reset_domain_analyzer import ResetIntegrityChecker
from trace.dependency import FanoutAnalyzer
from debug.analyzers.condition_coverage import ConditionCoverageAnalyzer
from debug.analyzers.timed_path_analyzer import TimedPathAnalyzer


TARGETED_DIR = os.path.join(os.path.dirname(__file__), 'targeted')


def test_fsm_corners():
    """FSM Corner Cases测试"""
    print("\n" + "="*60)
    print("FSM Corner Cases测试")
    print("="*60)
    
    test_file = os.path.join(TARGETED_DIR, 'test_fsm_corners.sv')
    parser = SVParser()
    parser.parse_file(test_file)
    
    analyzer = FSMAnalyzer(parser)
    report = analyzer.analyze()
    
    print(f"\n检测结果:")
    print(f"  状态数: {len(report.state_names)}")
    print(f"  跳转数: {len(report.transitions)}")
    print(f"  复杂度: {report.complexity.complexity_score} ({report.complexity.get_level()})")
    
    # 预期: One-hot, 三段式, 多状态机, 复杂条件, 非法状态恢复, 带计数器
    
    print(f"\n状态名: {report.state_names}")
    
    # SVA生成测试
    gen = SVAGenerator(parser)
    svap = gen.generate()
    print(f"\nSVA属性: {len(svap.properties)}")
    
    return True


def test_cdc_corners():
    """CDC Corner Cases测试"""
    print("\n" + "="*60)
    print("CDC Corner Cases测试")
    print("="*60)
    
    test_file = os.path.join(TARGETED_DIR, 'test_cdc_corners.sv')
    parser = SVParser()
    parser.parse_file(test_file)
    
    analyzer = CDCExtendedAnalyzer(parser)
    report = analyzer.analyze()
    
    print(f"\n检测结果:")
    print(f"  时钟域数: {len(report.clock_domains)}")
    print(f"  CDC路径数: {len(report.cdc_paths)}")
    print(f"  未保护信号: {len(report.unprotected_signals)}")
    
    for domain in report.clock_domains:
        print(f"  - {domain.name}: {domain.clock_signal}")
    
    for path in report.cdc_paths[:5]:
        print(f"  CDC: {path.signal} ({path.path_type})")
    
    return True


def test_condition_corners():
    """条件覆盖Corner Cases测试"""
    print("\n" + "="*60)
    print("条件覆盖Corner Cases测试")
    print("="*60)
    
    test_file = os.path.join(TARGETED_DIR, 'test_condition_corners.sv')
    parser = SVParser()
    parser.parse_file(test_file)
    
    analyzer = ConditionCoverageAnalyzer(parser)
    report = analyzer.analyze()
    
    print(f"\n检测结果:")
    print(f"  if语句数: {report.total_if_count}")
    print(f"  条件数: {report.total_conditions}")
    print(f"  cross对数: {sum(len(c.cross_pairs) for c in report.conditions)}")
    
    # 统计各种条件类型
    bit_select = 0
    compare = 0
    ternary = 0
    
    for cov in report.conditions:
        for branch in cov.branches:
            expr = branch.condition_expr.lower()
            if '[' in expr:
                bit_select += 1
            if any(op in expr for op in ['>', '<', '==', '!=']):
                compare += 1
            if '?' in expr:
                ternary += 1
    
    print(f"\n条件类型统计:")
    print(f"  位选择条件: {bit_select}")
    print(f"  比较条件: {compare}")
    print(f"  三元表达式: {ternary}")
    
    return True


def test_fanout_reset_corners():
    """Fanout和Reset Corner Cases测试"""
    print("\n" + "="*60)
    print("Fanout & Reset Corner Cases测试")
    print("="*60)
    
    test_file = os.path.join(TARGETED_DIR, 'test_fanout_reset_corners.sv')
    parser = SVParser()
    parser.parse_file(test_file)
    
    # Fanout测试
    print("\n[Fanout分析]")
    fanout = FanoutAnalyzer(parser)
    signals = list(set([s for s in fanout._fanout_cache.keys()]))
    print(f"  分析信号数: {len(signals)}")
    
    # 查找高扇出信号
    try:
        high_fo = fanout.find_high_fanout_signals(threshold=10)
        print(f"  高扇出信号(>10): {len(high_fo)}")
        for fo in high_fo[:5]:
            print(f"    - {fo.signal}: fanout={fo.direct_fanout}")
    except:
        print("  高扇出检测跳过")
    
    # Reset测试
    print("\n[Reset分析]")
    reset_checker = ResetIntegrityChecker(parser)
    report = reset_checker.check()
    
    print(f"  复位树节点: {len(report.reset_tree)}")
    print(f"  覆盖率: {report.coverage:.1f}%")
    
    for name, node in list(report.reset_tree.items())[:5]:
        print(f"    - {name}: fanout={node.fanout}")
    
    if report.warnings:
        print(f"\n  警告:")
        for w in report.warnings[:3]:
            print(f"    - {w}")
    
    return True


def test_all_corners():
    """运行所有Corner Case测试"""
    print("="*70)
    print("Corner Case综合测试")
    print("="*70)
    
    results = {}
    
    tests = [
        ("FSM Corner Cases", test_fsm_corners),
        ("CDC Corner Cases", test_cdc_corners),
        ("Condition Corner Cases", test_condition_corners),
        ("Fanout/Reset Corner Cases", test_fanout_reset_corners),
    ]
    
    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = "PASS" if result else "FAIL"
        except Exception as e:
            results[name] = f"FAIL: {str(e)[:50]}"
            import traceback
            traceback.print_exc()
    
    # 汇总
    print("\n" + "="*70)
    print("Corner Case测试汇总")
    print("="*70)
    
    for name, result in results.items():
        status = "✅" if result == "PASS" else "❌"
        print(f"  {status} {name}: {result}")
    
    all_pass = all(v == "PASS" for v in results.values())
    print(f"\n总体: {'✅ ALL PASS' if all_pass else '❌ SOME FAILED'}")
    
    return all_pass


if __name__ == "__main__":
    success = test_all_corners()
    sys.exit(0 if success else 1)
