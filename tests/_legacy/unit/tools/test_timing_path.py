"""
Timing Path 工具测试 (TDD)
目标: src/trace/timing_path.py
"""

import pytest
import sys
sys.path.insert(0, '../../src')
from parse import SVParser
from trace.timing_path import TimingPathExtractor

RTL_REG = '''module dut(input clk, input d, output q);
    logic r;
    always_ff @(posedge clk) r <= d;
    always_ff @(posedge clk) q <= r;
endmodule'''

RTL_COMB = '''module dut(input a, b, output y);
    assign y = a & b;
endmodule'''

class TestTimingPathBasic:
    @pytest.mark.unit
    def test_reg2reg(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_REG)
        tp = TimingPathExtractor(parser)
        tp.extract()
        assert tp.extract() is not None
    
    @pytest.mark.unit
    def test_comb(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_COMB)
        tp = TimingPathExtractor(parser)
        tp.extract()
        assert tp.extract() is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
