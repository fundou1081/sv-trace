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


# 更复杂的测试用例
COMPLEX_CASES = [
    ("fsm_state", [
        Condition('state==IDLE', 'if', 'condition'),
        Condition('state==RUN', 'if', 'condition'),
        Condition('state==DONE', 'if', 'condition'),
    ]),
    ("priority_encoder", [
        Condition('req[3]', 'if', 'condition'),
        Condition('req[2]', 'if', 'condition'),
        Condition('req[1]', 'if', 'condition'),
        Condition('req[0]', 'if', 'condition'),
    ]),
    ("alu_op", [
        Condition('op == ADD', 'if', 'condition'),
        Condition('op == SUB', 'if', 'condition'),
        Condition('op == MUL', 'if', 'condition'),
        Condition('op == DIV', 'if', 'condition'),
    ]),
    ("fifo_full", [
        Condition('wr_ptr == rd_ptr && wr_en', 'if', 'condition'),
        Condition('count == DEPTH', 'if', 'condition'),
        Condition('count == 0', 'if', 'condition'),
    ]),
    ("cdc_meta", [
        Condition('src_valid && !dst_ack', 'if', 'condition'),
        Condition('toggle_count == 2', 'if', 'condition'),
    ]),
    ("edge_detect", [
        Condition('!last_d && cur_d', 'if', 'condition'),
        Condition('last_d && !cur_d', 'if', 'condition'),
    ]),
    ("parity", [
        Condition('^data[7:0]', 'if', 'condition'),
        Condition('data[7]^data[6]^data[5]', 'if', 'condition'),
    ]),
    ("ack_timeout", [
        Condition('ack_valid && (timer > TIMEOUT)', 'if', 'condition'),
    ]),
]


def test_complex():
    print("\n=== Complex Cases ===")
    passed = 0
    for name, conds in COMPLEX_CASES:
        s = CoverageStimulusSuggester()
        s.conditions = conds
        s.coverage_points = [
            CoveragePoint(f'cp_{i}', c.expr, c.type, [])
            for i, c in enumerate(conds)
        ]
        
        try:
            cg = s.generate_covergroup(name)
            assert 'covergroup' in cg
            assert 'coverpoint' in cg
            print(f"  ✅ {name}: {len(conds)} conditions")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
    
    print(f"\nComplex: {passed}/{len(COMPLEX_CASES)} passed")
    return passed == len(COMPLEX_CASES)


if __name__ == '__main__':
    test_complex()
