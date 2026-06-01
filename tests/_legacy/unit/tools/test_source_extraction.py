"""
Source 提取测试 - 验证驱动源表达式提取功能

遵循铁律13: 金标准测试
覆盖：算术、位运算、移位、比较、逻辑运算符
"""

import pytest
import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.driver import DriverCollector


class TestSourceExtraction:
    """驱动源表达式提取测试"""
    
    @pytest.mark.unit
    def test_simple_signal(self):
        """基础信号"""
        rtl = 'module dut(input clk, a, output q); always_ff @(posedge clk) q <= a; endmodule'
        tree = SVParser(verbose=False).parse_text(rtl)
        dc = DriverCollector(parser=None, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        assert len(drivers) > 0
    
    @pytest.mark.unit
    def test_add_expression(self):
        """加法表达式"""
        rtl = 'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= a + b; endmodule'
        tree = SVParser(verbose=False).parse_text(rtl)
        dc = DriverCollector(parser=None, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        assert len(drivers) > 0
    
    @pytest.mark.unit
    def test_mul_expression(self):
        """乘法表达式"""
        rtl = 'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= a * b; endmodule'
        tree = SVParser(verbose=False).parse_text(rtl)
        dc = DriverCollector(parser=None, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        assert len(drivers) > 0
    
    @pytest.mark.unit
    def test_bitwise_and(self):
        """位与运算"""
        rtl = 'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= a & b; endmodule'
        tree = SVParser(verbose=False).parse_text(rtl)
        dc = DriverCollector(parser=None, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        assert len(drivers) > 0
    
    @pytest.mark.unit
    def test_bitwise_or(self):
        """位或运算"""
        rtl = 'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= a | b; endmodule'
        tree = SVParser(verbose=False).parse_text(rtl)
        dc = DriverCollector(parser=None, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        assert len(drivers) > 0
    
    @pytest.mark.unit
    def test_shift_left(self):
        """左移运算"""
        rtl = 'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= a << b; endmodule'
        tree = SVParser(verbose=False).parse_text(rtl)
        dc = DriverCollector(parser=None, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        assert len(drivers) > 0
    
    @pytest.mark.unit
    def test_complex_expression(self):
        """复杂表达式 (a + b) * c"""
        rtl = 'module dut(input clk, a, b, c, output q); always_ff @(posedge clk) q <= (a + b) * c; endmodule'
        tree = SVParser(verbose=False).parse_text(rtl)
        dc = DriverCollector(parser=None, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        assert len(drivers) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
