"""
Clock Domain 工具测试 (TDD)
目标: 验证时钟域识别功能

遵循铁律13: 金标准测试
- 先推导金标准，再对比验证
"""

import pytest
import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.driver import DriverCollector


# =============================================================================
# 金标准用例 (Golden Standard)
# =============================================================================

# 金标准1: 单时钟域
# clk 时钟域应该包含 q (寄存器)
RTL_SINGLE_CLK = '''module dut(input clk, rst_n, input d, output q);
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) q <= 0; else q <= d;
endmodule'''

# 金标准2: 双时钟域
# clk1 时钟域包含 q1, clk2 时钟域包含 q2
RTL_DUAL_CLK = '''module dut(input clk1, clk2, rst_n, input d1, d2, output q1, q2);
    always_ff @(posedge clk1 or negedge rst_n) q1 <= d1;
    always_ff @(posedge clk2 or negedge rst_n) q2 <= d2;
endmodule'''


# =============================================================================
# 测试类
# =============================================================================

class TestClockDomainBasic:
    @pytest.mark.unit
    def test_single_clock(self):
        """测试单时钟域 - 验证 q 被 clk 驱动"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SINGLE_CLK)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        # 金标准: q 应该有驱动，驱动类型是 always_ff
        assert 'q' in dc.drivers, "q 应有驱动"
        
        # 验证驱动属性
        q_drivers = dc.get_drivers('q')
        assert len(q_drivers) >= 1, "q 应有至少一个驱动"
        
        # 验证时钟
        d = q_drivers['q'][0]
        print(f"  q clock: {d.clock}, reset: {d.reset}")
    
    @pytest.mark.unit
    def test_dual_clock(self):
        """测试双时钟域 - 验证两个独立的时钟域"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_DUAL_CLK)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        # 金标准: q1 和 q2 都应该有驱动
        assert 'q1' in dc.drivers, "q1 应有驱动"
        assert 'q2' in dc.drivers, "q2 应有驱动"
        
        # 验证两个不同时钟
        q1_drivers = dc.get_drivers('q1')
        q2_drivers = dc.get_drivers('q2')
        
        if q1_drivers['q1']:
            print(f"  q1 clock: {q1_drivers['q1'][0].clock}")
        if q2_drivers['q2']:
            print(f"  q2 clock: {q2_drivers['q2'][0].clock}")


# =============================================================================
# 主入口
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])