"""
Clock Domain 工具测试 (TDD)
目标: src/trace/query/clock_domain.py
"""

import pytest
import sys
sys.path.insert(0, '../../src')
from parse import SVParser
from trace.query.clock_domain import ClockDomainTracer

# 单时钟域
RTL_SINGLE_CLK = '''module dut(input clk, rst_n, input d, output q);
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) q <= 0; else q <= d;
endmodule'''

# 双时钟域
RTL_DUAL_CLK = '''module dut(input clk1, clk2, rst_n, input d1, d2, output q1, q2);
    always_ff @(posedge clk1 or negedge rst_n) q1 <= d1;
    always_ff @(posedge clk2 or negedge rst_n) q2 <= d2;
endmodule'''

class TestClockDomainBasic:
    @pytest.mark.unit
    def test_single_clock(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SINGLE_CLK)
        cd = ClockDomainTracer(parser=parser, verbose=False)
        cd.collect(tree, 'dut.sv')
        assert cd is not None
    
    @pytest.mark.unit
    def test_dual_clock(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_DUAL_CLK)
        cd = ClockDomainTracer(parser=parser, verbose=False)
        cd.collect(tree, 'dut.sv')
        assert cd is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
