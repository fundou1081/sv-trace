#!/usr/bin/env python3
"""
CoverageStimulusSuggester Covergroup生成测试
"""
import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from verify.coverage_guide.stimulus_suggester import CoverageStimulusSuggester, Condition, CoveragePoint


TEST_CASES = [
    ("single_signal", "enable"),
    ("and_cond", "a && b"),
    ("or_cond", "a || b"),
    ("not_cond", "~enable"),
    ("compare", "count > 10"),
    ("nested", "(a && b) || c"),
    ("range", "data >= 8 && data <= 16"),
    ("multibit", "mode[1:0]"),
    ("equal", "data == 8'h55"),
    ("neq", "state != IDLE"),
]


def test_covergroup(name, expr):
    """测试covergroup生成"""
    s = CoverageStimulusSuggester()
    s.conditions = [Condition(expr, 'if', 'condition')]
    s.coverage_points = [CoveragePoint('cp_0', expr, 'if', [])]
    
    try:
        cg = s.generate_covergroup(name)
        # 验证生成
        assert 'covergroup' in cg
        assert 'coverpoint' in cg
        print(f"  ✅ {name}: {expr}")
        return True
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        return False


def main():
    print("=" * 60)
    print("Covergroup Generation Tests")
    print("=" * 60)
    
    passed = 0
    for name, expr in TEST_CASES:
        if test_covergroup(name, expr):
            passed += 1
    
    print("=" * 60)
    print(f"Result: {passed}/{len(TEST_CASES)} passed")
    print("=" * 60)
    
    return passed == len(TEST_CASES)


if __name__ == '__main__':
    main()
