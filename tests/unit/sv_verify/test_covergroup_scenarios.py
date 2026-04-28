#!/usr/bin/env python3
"""
CoverageStimulusSuggester 综合场景测试
"""
import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from verify.coverage_guide.stimulus_suggester import CoverageStimulusSuggester, Condition, CoveragePoint


SCENARIOS = [
    # FSM场景
    ("fsm_3state", [
        Condition('state==IDLE', 'if', 'condition'),
        Condition('state==RUN', 'if', 'condition'),
        Condition('state==DONE', 'if', 'condition'),
    ], 8),
    
    # 优先级encoder
    ("priority_enc", [
        Condition('req[3]', 'if', 'condition'),
        Condition('req[2]', 'if', 'condition'),
        Condition('req[1]', 'if', 'condition'),
        Condition('req[0]', 'if', 'condition'),
    ], 4),
    
    # ALU操作码
    ("alu_op", [
        Condition('op==ADD', 'if', 'condition'),
        Condition('op==SUB', 'if', 'condition'),
        Condition('op==MUL', 'if', 'condition'),
        Condition('op==DIV', 'if', 'condition'),
    ], 8),
    
    # FIFO状态
    ("fifo_status", [
        Condition('count==0', 'if', 'condition'),
        Condition('count==DEPTH', 'if', 'condition'),
        Condition('wr_ptr==rd_ptr', 'if', 'condition'),
    ], 16),
    
    # 边沿检测
    ("edge_detect", [
        Condition('!last && cur', 'if', 'condition'),
        Condition('last && !cur', 'if', 'condition'),
    ], 4),
    
    # CDC同步
    ("cdc_sync", [
        Condition('sync toggle', 'if', 'condition'),
        Condition('ack received', 'if', 'condition'),
    ], 8),
    
    # 仲裁器
    ("arbiter", [
        Condition('grant[0]', 'if', 'condition'),
        Condition('grant[1]', 'if', 'condition'),
        Condition('grant[2]', 'if', 'condition'),
        Condition('grant[3]', 'if', 'condition'),
    ], 8),
    
    # 奇偶校验
    ("parity", [
        Condition('parity_error', 'if', 'condition'),
        Condition('data_valid', 'if', 'condition'),
    ], 4),
    
    # 超时检测
    ("timeout", [
        Condition('timer>1000', 'if', 'condition'),
        Condition('timer>5000', 'if', 'condition'),
    ], 4),
    
    # 错误检测
    ("error_detect", [
        Condition('crc_error', 'if', 'condition'),
        Condition('ecc_error', 'if', 'condition'),
        Condition('parity_err', 'if', 'condition'),
    ], 8),
]


def test_generate_bins_only():
    """仅测试generate_bins"""
    print("=== generate_bins 测试 ===\n")
    
    tests = [
        ("enable", 1, ""),
        ("data", 8, ""),
        ("addr", 16, ""),
        ("cond", 1, "a & b"),
        ("result", 1, "x ^ y"),
    ]
    
    s = CoverageStimulusSuggester()
    
    for name, width, expr in tests:
        try:
            bins = s.generate_bins(name, width, expr)
            print(f"✅ {name} (width={width})")
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    print()


def test_scenarios():
    """测试完整场景"""
    print("=== 场景测试 ===\n")
    
    passed = 0
    for name, conds, expected_lines in SCENARIOS:
        s = CoverageStimulusSuggester()
        s.conditions = conds
        s.coverage_points = [
            CoveragePoint(f'cp_{i}', c.expr, c.type, [])
            for i, c in enumerate(conds)
        ]
        
        try:
            cg = s.generate_covergroup(name)
            lines = cg.split('\n')
            
            # 验证
            has_covergroup = 'covergroup' in cg
            has_coverpoint = 'coverpoint' in cg
            
            if has_covergroup and has_coverpoint:
                print(f"✅ {name}: {len(conds)} conditions, {len(lines)} lines")
                passed += 1
            else:
                print(f"❌ {name}: missing elements")
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    print(f"\n结果: {passed}/{len(SCENARIOS)} 通过")
    return passed == len(SCENARIOS)


if __name__ == '__main__':
    test_generate_bins_only()
    test_scenarios()
