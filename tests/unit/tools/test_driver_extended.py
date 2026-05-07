"""
Driver 扩展金标准测试 - 更多复杂场景

包含：
- always_latch
- force/release
- clock gating
- 多个 always 块
- casez/casex
- 优先级编码
"""

import pytest
import sys
sys.path.insert(0, 'src')
from parse import SVParser
from trace.driver import DriverCollector


# =============================================================================
# 金标准 P3: 扩展场景
# =============================================================================

# P3-1: always_latch
RTL_LATCH = '''module dut(input data, output logic q);
    always_latch if (data) q = 1;
endmodule'''

# P3-2: force 语句
RTL_FORCE = '''module dut(input data, output logic q);
    initial force q = data;
endmodule'''

# P3-3: 多 always 块
RTL_MULTI_ALWAYS = '''module dut(
    input  logic clk, rst_n,
    input  logic a, b,
    output logic q1, q2
);
    always_ff @(posedge clk or negedge rst_n)
        q1 <= a;
    always_ff @(posedge clk)
        q2 <= b;
endmodule'''

# P3-4: casez
RTL_CASEZ = '''module dut(input [3:0] sel, output logic q);
    always_comb casez (sel)
        4'b1???: q = 1;
        4'b0???: q = 0;
    endcasez
endmodule'''

# P3-5: 优先级编码
RTL_PRIORITY = '''module dut(input a, b, output logic y);
    always_comb begin
        if (a) y = 1;
        else if (b) y = 1;
        else y = 0;
    end
endmodule'''

# P3-6: 门控时钟
RTL_CLOCK_GATE = '''module dut(
    input  logic clk,
    input  logic clk_en,
    input  logic d,
    output logic q
);
    logic gclk;
    assign gclk = clk & clk_en;
    always_ff @(posedge gclk)
        q <= d;
endmodule'''

# P3-7: 双向口
RTL_INOUT = '''module dut(
    inout  logic data,
    input  logic oe,
    input  logic data_in
);
    assign data = oe ? data_in : 1'bz;
endmodule'''

# P3-8: generate if
RTL_GEN_IF = '''module dut(
    input  logic clk,
    input  logic gen_en,
    input  logic d,
    output logic q
);
    generate
        if (gen_en) begin : gen_block
            always_ff @(posedge clk)
                q <= d;
        end
    endgenerate
endmodule'''


# =============================================================================
# 测试
# =============================================================================

class TestDriverExtended:
    @pytest.mark.unit
    def test_latch(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_LATCH)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        print(f"  latch drivers: {dc.drivers}")
    
    @pytest.mark.unit
    def test_force(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_FORCE)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        print(f"  force: {dc.drivers}")
    
    @pytest.mark.unit
    def test_multi_always(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_MULTI_ALWAYS)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        print(f"  q1: {dc.get_drivers('q1')}")
        print(f"  q2: {dc.get_drivers('q2')}")
        assert len(dc.drivers) >= 2
    
    @pytest.mark.unit
    def test_casez(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CASEZ)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        print(f"  casez drivers: {dc.drivers}")
    
    @pytest.mark.unit
    def test_clock_gate(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CLOCK_GATE)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        print(f"  gclk: {dc.all_clocks}")
        # 门控时钟
    
    @pytest.mark.unit
    def test_gen_if(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_GEN_IF)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        print(f"  gen drivers: {dc.drivers}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
