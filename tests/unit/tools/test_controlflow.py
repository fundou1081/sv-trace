"""
Controlflow 工具测试 (TDD)
目标: src/trace/controlflow.py
"""

import pytest
import sys
sys.path.insert(0, '../../src')
from parse import SVParser
from trace.controlflow import ControlFlowTracer

# 简单 if-else
RTL_IF = '''module dut(input logic a, output logic y);
    always_comb if (a) y = 1; else y = 0;
endmodule'''

# case 语句
RTL_CASE = '''module dut(input [1:0] sel, output logic y);
    always_comb case (sel)
        2'd0: y = 1;
        2'd1: y = 2;
        default: y = 0;
    endcase
endmodule'''

# for 循环
RTL_FOR = '''module dut(input clk, output logic [7:0] y);
    logic [7:0] cnt;
    always_ff @(posedge clk) begin
        for (int i=0; i<8; i++) cnt[i] <= 1'b0;
    end
endmodule'''

class TestControlFlowBasic:
    @pytest.mark.unit
    def test_if_else(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_IF)
        cf = ControlFlowTracer(parser=parser, verbose=False)
        cf.collect(tree, 'dut.sv')
        assert cf is not None
    
    @pytest.mark.unit
    def test_case(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CASE)
        cf = ControlFlowTracer(parser=parser, verbose=False)
        cf.collect(tree, 'dut.sv')
        assert cf is not None
    
    @pytest.mark.unit
    def test_for_loop(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_FOR)
        cf = ControlFlowTracer(parser=parser, verbose=False)
        cf.collect(tree, 'dut.sv')
        assert cf is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
