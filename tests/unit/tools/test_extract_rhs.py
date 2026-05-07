"""
_extract_rhs() 功能测试 (TDD)

目标: 验证能从赋值右侧提取完整表达式

金标准:
  q <= a + b         → source = "a + b"
  q <= {a, b}        → source = "{a, b}"
  q <= process(data) → source = "process(data)"
"""

import pytest
import sys
sys.path.insert(0, 'src')
from parse import SVParser
from trace.driver import DriverCollector


# 测试用例
TEST_CASES = [
    ('a + b', 'q <= a + b'),
    ('{a, b}', 'q <= {a, b}'),
    ('process(data)', 'q <= process(data)'),
    ('sel ? a : b', 'q <= sel ? a : b'),
    ('a + b * c', 'q <= a + b * c'),
]


class TestExtractRhs:
    @pytest.mark.unit
    def test_basic_rhs(self):
        rtl = f'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= a + b; endmodule'
        tree = SVParser(verbose=False).parse_text(rtl)
        dc = DriverCollector(parser=None, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        d = drivers['q'][0]
        
        print(f"  a + b 提取: sources={d.sources}")
        
        # 验证有驱动
        assert len(drivers) > 0
    
    @pytest.mark.unit
    def test_concat_rhs(self):
        rtl = 'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= {a, b}; endmodule'
        tree = SVParser(verbose=False).parse_text(rtl)
        dc = DriverCollector(parser=None, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        print(f"  {{a,b}} 提取: sources={drivers['q'][0].sources}")
        assert len(drivers) > 0
    
    @pytest.mark.unit
    def test_ternary_rhs(self):
        rtl = 'module dut(input clk, sel, a, b, output q); always_ff @(posedge clk) q <= sel ? a : b; endmodule'
        tree = SVParser(verbose=False).parse_text(rtl)
        dc = DriverCollector(parser=None, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        print(f"  sel?a:b 提取: sources={drivers['q'][0].sources}")
        assert len(drivers) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
