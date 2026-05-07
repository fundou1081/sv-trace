"""
Module Connections 工具测试 (TDD)
"""
import pytest
import sys
sys.path.insert(0, 'src')
from query.module_connections import ModuleConnectionsQuery

RTL = '''module dut(input clk, input d, output q);
    sub u_sub(clk, d, q);
endmodule
module sub(input clk, input d, output q);
    always_ff @(posedge clk) q <= d;
endmodule'''

class TestBasic:
    @pytest.mark.unit
    def test_connections(self):
        mc = ModuleConnectionsQuery(trees={}, verbose=False)
        mc.collect(RTL, 'dut.sv')
        assert mc is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
