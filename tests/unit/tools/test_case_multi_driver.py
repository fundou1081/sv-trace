"""
Case 多驱动金标准测试 (TDD)
"""

import pytest
import sys
sys.path.insert(0, 'src')
from parse import SVParser
from trace.driver import DriverCollector


RTL_CASE_MULTI = '''module dut(
    input  logic clk,
    input  logic rst_n,
    input  logic [1:0] sel,
    input  logic [7:0] d0, d1, d2, d3,
    output logic [7:0] q
);
    always_ff @(posedge clk or negedge rst_n) begin
        case (sel)
            2'd0: q <= d0;
            2'd1: q <= d1;
            2'd2: q <= d2;
            default: q <= d3;
        endcase
    end
endmodule'''


class TestCaseMultiDriver:
    @pytest.mark.unit
    def test_case_multi_driver(self):
        """Case 语句多驱动 - 金标准验证"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CASE_MULTI)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        # 1. 有驱动
        drivers = dc.get_drivers('q')
        assert len(drivers) >= 1
        
        # 2. case 多驱动检测 (核心)
        is_multi = hasattr(dc, 'multi_drivers') and 'q' in dc.multi_drivers
        print(f"  multi_drivers: {dc.multi_drivers}")
        
        assert is_multi, "case 语句应标记为多驱动系统"
        
        # 3. 输出验证
        for d in drivers.get('q', []):
            print(f"    signal={d.signal}, kind={d.kind}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
