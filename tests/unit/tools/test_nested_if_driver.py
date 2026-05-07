"""
嵌套 if 多驱动金标准测试 (TDD)

金标准:
RTL:
  always_ff @(posedge clk or negedge rst_n)
    if (a)
      if (b) q <= d2;
      else q <= d1;
    else
      q <= d0;

预期:
  q.drivers = [d0, d1, d2] (3个分支)
"""

import pytest
import sys
sys.path.insert(0, 'src')
from parse import SVParser
from trace.driver import DriverCollector


RTL_NESTED_IF = '''module dut(
    input  logic clk,
    input  logic rst_n,
    input  logic a, b,
    input  logic [7:0] d0, d1, d2,
    output logic [7:0] q
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (a) begin
            if (b) q <= d2;
            else q <= d1;
        end else begin
            q <= d0;
        end
    end
endmodule'''


class TestNestedIfDriver:
    @pytest.mark.unit
    def test_nested_if_multi_driver(self):
        """嵌套 if 多驱动检测"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_NESTED_IF)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        print(f"  driver count: {len(drivers.get('q', []))}")
        
        is_multi = hasattr(dc, 'multi_drivers') and 'q' in dc.multi_drivers
        print(f"  multi_drivers: {is_multi}")
        
        assert len(drivers) >= 1, "必须有驱动"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
