"""
Signal Chain 工具测试 (TDD)
"""
import pytest
import sys
sys.path.insert(0, 'src')
from query.signal_chain import SignalChainQuery

RTL = '''module dut(input clk, input d, output q);
    logic r;
    always_ff @(posedge clk) r <= d;
    always_ff @(posedge clk) q <= r;
endmodule'''

class TestBasic:
    @pytest.mark.unit
    def test_signal_chain(self):
        sc = SignalChainQuery(trees={}, verbose=False)
        sc.collect(RTL, 'dut.sv')
        assert sc is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
