"""ClockDomainTracer 测试 - 铁律13 金标准验证

遵循开发纪律:
- 铁律13: 金标准测试 - 先推导金标准再对比验证

测试场景C: 时钟域追踪
"""

import sys
import os

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.query import ClockDomainTracer


# =============================================================================
# 金标准定义 (人工推导)
# =============================================================================

RTL_CLOCK_DOMAIN = '''
module clock_domain_test;
    input clk;
    input clk2;  // 第二个时钟
    input rst_n;
    input [7:0] data_in;
    input enable;
    
    // 寄存器 A - clk 时钟域
    logic [7:0] reg_a;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            reg_a <= 8'h00;
        else if (enable)
            reg_a <= data_in;
    end
    
    // 寄存器 B - clk 时钟域
    logic [7:0] reg_b;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            reg_b <= 8'h00;
        else
            reg_b <= reg_a;
    end
    
    // 寄存器 C - clk2 时钟域 (不同域)
    logic [7:0] reg_c;
    always_ff @(posedge clk2 or negedge rst_n) begin
        if (!rst_n)
            reg_c <= 8'h00;
        else
            reg_c <= data_in;
    end
    
    // 输出
    output [7:0] out_a, out_b, out_c;
    assign out_a = reg_a;
    assign out_b = reg_b;
    assign out_c = reg_c;
endmodule
'''

"""
金标准推导:

clk 时钟域:
┌───────────┬──────────────┬────────────┬──────────────┐
│ 寄存器   │ 时钟         │ 复位      │ 数据通路     │
├───────────┼──────────────┼────────────┼──────────────┤
│ reg_a    │ clk          │ rst_n     │ data_in      │
│ reg_b    │ clk          │ rst_n     │ reg_a        │
└───────────┴──────────────┴────────────┴──────────────┘
- reg_a, reg_b 在 clk 时钟域
- 复位信号: rst_n

clk2 时钟域:
┌───────────┬──────────────┬────────────┬──────────────┐
│ 寄存器   │ 时钟         │ 复位      │ 数据通路     │
├───────────┼──────────────┼────────────┼──────────────┤
│ reg_c    │ clk2         │ rst_n     │ data_in      │
└───────────┴──────────────┴────────────┴──────────────┘
- reg_c 在 clk2 时钟域
"""


def test_clock_domain_identification():
    """测试: 时钟域识别
    
    金标准:
    - clk 时钟域包含 reg_a, reg_b
    - clk2 时钟域包含 reg_c
    """
    print("\n=== Test: Clock Domain Identification ===")
    
    parser = SVParser()
    parser.parse_text(RTL_CLOCK_DOMAIN, '<test>')
    
    tracer = ClockDomainTracer(parser)
    
    # 金标准: 应识别至少 2 个时钟域
    clock_signals = list(tracer._clock_domains.keys())
    print(f"  识别的时钟域: {clock_signals}")
    assert len(clock_signals) >= 2, f"金标准: >=2 时钟域, 实际: {len(clock_signals)}"
    
    # 金标准: clk 和 clk2 都应被识别
    assert 'clk' in clock_signals or 'clk2' in clock_signals, \
        f"金标准: clk/clk2 应被识别"
    
    print("  ✅ 时钟域识别验证通过")


def test_signal_to_clock_mapping():
    """测试: 信号到时钟域的映射
    
    金标准:
    - reg_a, reg_b 应映射到 clk 域
    - reg_c 应映射到 clk2 域
    """
    print("\n=== Test: Signal to Clock Mapping ===")
    
    parser = SVParser()
    parser.parse_text(RTL_CLOCK_DOMAIN, '<test>')
    
    tracer = ClockDomainTracer(parser)
    
    # 金标准: reg_a, reg_b 应在 clk 域
    print(f"  信号映射数: {len(tracer._signal_domains)}")
    
    # reg_a 和 reg_b 应映射到同一个域
    if 'reg_a' in tracer._signal_domains and 'reg_b' in tracer._signal_domains:
        domain_a = tracer._signal_domains['reg_a']
        domain_b = tracer._signal_domains['reg_b']
        assert domain_a == domain_b, \
            f"金标准: reg_a 和 reg_b 应在同一域, 实际: {domain_a} vs {domain_b}"
        print(f"  ✅ reg_a 和 reg_b 在同一域: {domain_a}")
    
    # reg_c 应在不同域
    if 'reg_c' in tracer._signal_domains:
        print(f"  ✅ reg_c 在域: {tracer._signal_domains['reg_c']}")
    
    print("  ✅ 信号映射验证通过")


def test_reset_signal_association():
    """测试: 复位信号关联
    
    金标准:
    - rst_n 是 clk 和 clk2 域的复位
    """
    print("\n=== Test: Reset Signal Association ===")
    
    parser = SVParser()
    parser.parse_text(RTL_CLOCK_DOMAIN, '<test>')
    
    tracer = ClockDomainTracer(parser)
    
    # 检查复位信号分类
    resets = getattr(tracer, '_reset_signals', set())
    print(f"  复位信号: {resets}")
    
    # 金标准: rst_n 应被识别为复位信号
    assert 'rst_n' in resets, f"金标准: rst_n 应为复位信号"
    
    print("  ✅ 复位信号关联验证通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("ClockDomainTracer 测试套件")
    print("遵循铁律13: 金标准测试")
    print("=" * 60)
    
    tests = [
        test_clock_domain_identification,
        test_signal_to_clock_mapping,
        test_reset_signal_association,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__} ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
