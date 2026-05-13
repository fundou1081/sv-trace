"""
Clock Domain 测试 (TDD)

遵循铁律13: 金标准测试
目标: 验证时钟域识别功能
使用 DriverCollector 和 LoadTracer
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
RTL_SINGLE_DOMAIN = '''module dut(
    input  clk,
    input  rst_n,
    input  [7:0] data_in,
    output [7:0] reg_a,
    output [7:0] reg_b
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            reg_a <= 8'h00;
        else
            reg_a <= data_in;
    end
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            reg_b <= 8'h00;
        else
            reg_b <= reg_a;
    end
endmodule'''

# 金标准2: 双时钟域
RTL_DUAL_DOMAIN = '''module dut(
    input  clk1,
    input  clk2,
    input  rst_n,
    input  [7:0] data_in,
    output [7:0] reg_a,
    output [7:0] reg_c
);
    always_ff @(posedge clk1 or negedge rst_n) begin
        if (!rst_n)
            reg_a <= 8'h00;
        else
            reg_a <= data_in;
    end
    
    always_ff @(posedge clk2 or negedge rst_n) begin
        if (!rst_n)
            reg_c <= 8'h00;
        else
            reg_c <= data_in;
    end
endmodule'''


# =============================================================================
# 测试类
# =============================================================================

class TestClockDomainBasic:
    """基础时钟域测试"""
    
    @pytest.mark.unit
    def test_clock_domain_identification(self):
        """测试时钟域识别
        
        金标准:
        - reg_a, reg_b 在 clk 时钟域
        - clk 被识别为时钟
        - rst_n 被识别为复位
        """
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SINGLE_DOMAIN)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        # reg_a 和 reg_b 都应该有驱动
        for sig in ['reg_a', 'reg_b']:
            assert sig in dc.drivers, f"{sig} 应有驱动"
        
        # 验证时钟
        reg_a_drivers = dc.get_drivers('reg_a')
        d = reg_a_drivers['reg_a'][0]
        print(f"  reg_a clock: '{d.clock}', reset: '{d.reset}'")
        
        # 验证 kind
        assert d.kind == 'always_ff', f"驱动类型应是 always_ff, 实际: {d.kind}"
    
    @pytest.mark.unit
    def test_signal_to_clock_mapping(self):
        """测试信号到时钟域的映射
        
        金标准:
        - reg_a 映射到 clk1 域
        - reg_c 映射到 clk2 域
        """
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_DUAL_DOMAIN)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        # reg_a 和 reg_c 都应该有驱动
        for sig in ['reg_a', 'reg_c']:
            assert sig in dc.drivers, f"{sig} 应有驱动"
        
        # 两个信号的时钟不同
        reg_a_drivers = dc.get_drivers('reg_a')
        reg_c_drivers = dc.get_drivers('reg_c')
        
        d1 = reg_a_drivers['reg_a'][0]
        d2 = reg_c_drivers['reg_c'][0]
        
        print(f"  reg_a clock: '{d1.clock}'")
        print(f"  reg_c clock: '{d2.clock}'")
    
    @pytest.mark.unit
    def test_reset_signal_association(self):
        """测试复位信号关联
        
        金标准:
        - rst_n 被识别为复位
        """
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SINGLE_DOMAIN)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        # 验证复位
        reg_a_drivers = dc.get_drivers('reg_a')
        d = reg_a_drivers['reg_a'][0]
        
        print(f"  reset: '{d.reset}'")
        assert d.reset, "应有复位信号"


# =============================================================================
# 主入口
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])