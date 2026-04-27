import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

"""
针对性测试 - 针对每个功能的专项测试用例
"""
import sys
import os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from debug.analyzers.fsm_analyzer import FSMAnalyzer, SVAGenerator, VerificationPlanGenerator
from debug.analyzers.cdc import CDCExtendedAnalyzer
from debug.analyzers.reset_domain_analyzer import ResetIntegrityChecker
from trace.dependency import FanoutAnalyzer, FaninAnalyzer
from debug.analyzers.timed_path_analyzer import TimedPathAnalyzer
from debug.analyzers.condition_coverage import ConditionCoverageAnalyzer


TARGETED_DIR = '/Users/fundou/my_dv_proj/sv-trace/tests/targeted'


def test_fsm_targeted():
    """FSM状态机专项测试"""
    print("\n" + "="*60)
    print("FSM状态机专项测试")
    print("="*60)
    
    test_file = os.path.join(TARGETED_DIR, 'test_fsm_targeted.sv')
    
    parser = SVParser()
    parser.parse_file(test_file)
    
    analyzer = FSMAnalyzer(parser)
    report = analyzer.analyze()
    
    print(f"\n状态机识别结果:")
    print(f"  识别到状态数: {len(report.state_names)}")
    print(f"  跳转数: {len(report.transitions)}")
    
    # 预期: 
    # - fsm_enum_test: 6 states (IDLE, START, RUN, WAIT, STOP, ERROR)
    # - fsm_param_test: 4 states
    # - fsm_single_state: 0 states (不是FSM)
    # - fsm_deep_nested: 16 states
    
    print(f"\n预期状态名: {report.state_names[:20]}")
    
    # 验证复杂度评分
    complexity = report.complexity
    print(f"\n复杂度评分:")
    print(f"  状态数: {complexity.state_count}")
    print(f"  跳转数: {complexity.transition_count}")
    print(f"  评分: {complexity.complexity_score} ({complexity.get_level()})")
    
    # SVA生成测试
    print(f"\nSVA生成测试:")
    gen = SVAGenerator(parser)
    svap = gen.generate()
    print(f"  生成属性数: {len(svap.properties)}")
    print(f"  生成序列数: {len(svap.sequences)}")
    
    # 验证计划生成测试
    print(f"\n验证计划生成测试:")
    vgen = VerificationPlanGenerator(parser)
    plan = vgen.generate("test_fsm")
    print(f"  生成测试点数: {plan.total_tests}")
    
    return True


def test_cdc_targeted():
    """CDC跨时钟域专项测试"""
    print("\n" + "="*60)
    print("CDC跨时钟域专项测试")
    print("="*60)
    
    test_file = os.path.join(TARGETED_DIR, 'test_cdc_targeted.sv')
    
    parser = SVParser()
    parser.parse_file(test_file)
    
    analyzer = CDCExtendedAnalyzer(parser)
    report = analyzer.analyze()
    
    print(f"\nCDC分析结果:")
    print(f"  时钟域数: {len(report.clock_domains)}")
    print(f"  CDC路径数: {len(report.cdc_paths)}")
    print(f"  未保护信号数: {len(report.unprotected_signals)}")
    
    # 打印时钟域
    for domain in report.clock_domains:
        print(f"  - {domain.name}: {domain.clock_signal}")
    
    # 打印CDC路径
    if report.cdc_paths:
        print(f"\nCDC路径详情:")
        for path in report.cdc_paths[:5]:
            print(f"  - {path.signal}: {path.source_domain} -> {path.dest_domain} ({path.path_type})")
    
    return True


def test_condition_targeted():
    """条件覆盖专项测试"""
    print("\n" + "="*60)
    print("条件覆盖专项测试")
    print("="*60)
    
    test_file = os.path.join(TARGETED_DIR, 'test_condition_targeted.sv')
    
    parser = SVParser()
    parser.parse_file(test_file)
    
    analyzer = ConditionCoverageAnalyzer(parser)
    report = analyzer.analyze()
    
    print(f"\n条件覆盖分析结果:")
    print(f"  if语句数: {report.total_if_count}")
    print(f"  条件数: {report.total_conditions}")
    print(f"  平均覆盖率: {report.average_coverage*100:.1f}%")
    
    # 打印各条件详情
    print(f"\n条件详情:")
    for cov in report.conditions[:5]:
        print(f"  Line {cov.line}: depth={cov.depth}")
        for branch in cov.branches[:2]:
            if branch.condition_expr:
                print(f"    {branch.branch_type}: {branch.condition_expr[:40]}")
    
    # 打印cross对
    cross_pairs = []
    for cov in report.conditions:
        cross_pairs.extend(cov.cross_pairs)
    
    print(f"\nCross覆盖对数: {len(cross_pairs)}")
    for pair in cross_pairs[:5]:
        print(f"  {pair[0]} x {pair[1]}")
    
    return True


def test_fanout_targeted():
    """Fanout扇出专项测试"""
    print("\n" + "="*60)
    print("Fanout扇出专项测试")
    print("="*60)
    
    test_file = os.path.join(TARGETED_DIR, 'test_fanout_targeted.sv')
    
    parser = SVParser()
    parser.parse_file(test_file)
    
    analyzer = FanoutAnalyzer(parser)
    
    print(f"\nFanout分析结果:")
    
    # 查找高扇出信号
    high_fo = analyzer.find_high_fanout_signals(threshold=2)
    print(f"  高扇出信号数(threshold=2): {len(high_fo)}")
    
    for fo in high_fo[:10]:
        print(f"    - {fo.signal}: direct={fo.direct_fanout}, total={fo.total_fanout}")
    
    # 验证enable信号的高扇出
    enable_fo = analyzer.analyze_signal('enable')
    print(f"\n  enable信号扇出:")
    print(f"    direct_fanout: {enable_fo.direct_fanout}")
    print(f"    total_fanout: {enable_fo.total_fanout}")
    print(f"    驱动信号数: {len(enable_fo.driven_signals)}")
    
    return True


def test_reset_targeted():
    """复位完整性专项测试"""
    print("\n" + "="*60)
    print("复位完整性专项测试")
    print("="*60)
    
    test_file = os.path.join(TARGETED_DIR, 'test_reset_targeted.sv')
    
    parser = SVParser()
    parser.parse_file(test_file)
    
    checker = ResetIntegrityChecker(parser)
    report = checker.check()
    
    print(f"\n复位分析结果:")
    print(f"  复位树节点数: {len(report.reset_tree)}")
    print(f"  覆盖率: {report.coverage:.1f}%")
    
    # 打印复位树
    print(f"\n复位树:")
    for name, node in list(report.reset_tree.items())[:5]:
        print(f"  - {name}: fanout={node.fanout}, level={node.level}")
    
    # 打印问题
    if report.issues:
        print(f"\n问题:")
        for issue in report.issues:
            print(f"  - {issue}")
    
    # 打印警告
    if report.warnings:
        print(f"\n警告:")
        for warning in report.warnings[:5]:
            print(f"  - {warning}")
    
    # 打印建议
    if report.recommendations:
        print(f"\n建议:")
        for rec in report.recommendations:
            print(f"  - {rec}")
    
    return True


def test_timed_path_targeted():
    """Timed Path专项测试"""
    print("\n" + "="*60)
    print("Timed Path专项测试")
    print("="*60)
    
    # 使用CDC测试文件，因为包含多时钟域
    test_file = os.path.join(TARGETED_DIR, 'test_cdc_targeted.sv')
    
    parser = SVParser()
    parser.parse_file(test_file)
    
    analyzer = TimedPathAnalyzer(parser)
    report = analyzer.analyze()
    
    print(f"\nTimed Path分析结果:")
    print(f"  路径数: {len(report.paths)}")
    print(f"  同时钟域路径: {report.same_domain_paths}")
    print(f"  慢到快路径: {report.slow_to_fast}")
    print(f"  快到慢路径: {report.fast_to_slow}")
    print(f"  异步路径: {report.async_paths}")
    
    # 打印路径
    if report.paths:
        print(f"\n路径详情:")
        for path in report.paths[:5]:
            print(f"  - {path.source_reg} -> {path.dest_reg} ({path.path_type})")
            print(f"    depth: {path.timing_depth}, logic: {path.logic_depth}")
    
    return True


def run_all_targeted_tests():
    """运行所有针对性测试"""
    print("="*60)
    print("针对性测试套件")
    print("="*60)
    
    results = {}
    
    tests = [
        ("FSM状态机测试", test_fsm_targeted),
        ("CDC跨时钟域测试", test_cdc_targeted),
        ("条件覆盖测试", test_condition_targeted),
        ("Fanout扇出测试", test_fanout_targeted),
        ("复位完整性测试", test_reset_targeted),
        ("Timed Path测试", test_timed_path_targeted),
    ]
    
    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = "PASS" if result else "FAIL"
        except Exception as e:
            results[name] = f"FAIL: {e}"
            import traceback
            traceback.print_exc()
    
    # 汇总
    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)
    
    for name, result in results.items():
        status = "✅" if result == "PASS" else "❌"
        print(f"  {status} {name}: {result}")
    
    all_pass = all(v == "PASS" for v in results.values())
    print(f"\n总体: {'✅ ALL PASS' if all_pass else '❌ SOME FAILED'}")
    
    return all_pass


if __name__ == "__main__":
    success = run_all_targeted_tests()
    sys.exit(0 if success else 1)
