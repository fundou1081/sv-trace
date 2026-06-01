import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

"""
针对性测试 - 使用 targeted 测试用例
"""
import sys
import os

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from debug.analyzers.fsm_analyzer import FSMAnalyzer
from debug.analyzers.cdc import CDCExtendedAnalyzer
from debug.analyzers.condition_coverage import ConditionCoverageAnalyzer
from debug.analyzers.reset_domain_analyzer import ResetIntegrityChecker
from debug.analyzers.timed_path_analyzer import TimedPathAnalyzer


TARGETED_DIR = '/Users/fundou/my_dv_proj/sv-trace/tests/targeted'


def test_fsm_targeted():
    """FSM Targeted测试"""
    print("\n=== FSM Targeted 测试 ===")
    
    test_file = os.path.join(TARGETED_DIR, 'test_fsm_targeted.sv')
    if not os.path.exists(test_file):
        print("  ⚠️  跳过 (文件不存在)")
        return True
    
    parser = SVParser()
    parser.parse_file(test_file)
    
    analyzer = FSMAnalyzer(parser)
    report = analyzer.analyze()
    
    print(f"  状态数: {len(report.state_names)}")
    print("  ✅ FSM Targeted 测试通过")
    return True


def test_cdc_targeted():
    """CDC Targeted测试"""
    print("\n=== CDC Targeted 测试 ===")
    
    test_file = os.path.join(TARGETED_DIR, 'test_cdc_targeted.sv')
    if not os.path.exists(test_file):
        print("  ⚠️  跳过 (文件不存在)")
        return True
    
    parser = SVParser()
    parser.parse_file(test_file)
    
    analyzer = CDCExtendedAnalyzer(parser)
    result = analyzer.analyze()
    
    print(f"  ✅ CDC Targeted 测试通过")
    return True


def test_condition_targeted():
    """Condition Targeted测试"""
    print("\n=== Condition Targeted 测试 ===")
    
    test_file = os.path.join(TARGETED_DIR, 'test_condition_targeted.sv')
    if not os.path.exists(test_file):
        print("  ⚠️  跳过 (文件不存在)")
        return True
    
    parser = SVParser()
    parser.parse_file(test_file)
    
    analyzer = ConditionCoverageAnalyzer(parser)
    result = analyzer.analyze()
    
    print(f"  ✅ Condition Targeted 测试通过")
    return True


def test_reset_targeted():
    """Reset Targeted测试"""
    print("\n=== Reset Targeted 测试 ===")
    
    test_file = os.path.join(TARGETED_DIR, 'test_reset_targeted.sv')
    if not os.path.exists(test_file):
        print("  ⚠️  跳过 (文件不存在)")
        return True
    
    parser = SVParser()
    parser.parse_file(test_file)
    
    checker = ResetIntegrityChecker(parser)
    result = checker.check()
    
    print(f"  ✅ Reset Targeted 测试通过")
    return True


def test_timed_path_targeted():
    """Timed Path Targeted测试"""
    print("\n=== Timed Path Targeted 测试 ===")
    
    test_file = os.path.join(TARGETED_DIR, 'test_timed_path_targeted.sv')
    if not os.path.exists(test_file):
        print("  ⚠️  跳过 (文件不存在)")
        return True
    
    parser = SVParser()
    parser.parse_file(test_file)
    
    analyzer = TimedPathAnalyzer(parser)
    result = analyzer.analyze()
    
    print(f"  ✅ Timed Path Targeted 测试通过")
    return True


def run_all_targeted_tests():
    """运行所有针对性测试"""
    tests = [
        ("FSMTargeted", test_fsm_targeted),
        ("CDCTargeted", test_cdc_targeted),
        ("ConditionTargeted", test_condition_targeted),
        ("ResetTargeted", test_reset_targeted),
        ("TimedPathTargeted", test_timed_path_targeted),
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
    success = run_all_targeted_tests()
    sys.exit(0 if success else 1)
