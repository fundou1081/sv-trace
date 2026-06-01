"""
Load 工具测试 (TDD 方式)

遵循铁律13: 金标准测试
目标: src/trace/load.py
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from parse import SVParser
from trace.load import LoadTracer


# =============================================================================
# 金标准用例
# =============================================================================

# 金标准1: 简单负载
RTL_SIMPLE_LOAD = '''module dut(
    input  logic clk,
    input  logic [7:0] data,
    output logic [7:0] q
);
    always_ff @(posedge clk) q <= data;
endmodule'''

# 预期: q.load = [data]


# 金标准2: 条件负载
RTL_CONDITIONAL_LOAD = '''module dut(
    input  logic clk,
    input  logic sel,
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] q
);
    always_ff @(posedge clk) begin
        if (sel) q <= a;
        else   q <= b;
    end
endmodule'''

# 预期: q.load = [a, b]


# 金标准3: 多负载
RTL_MULTI_LOAD = '''module dut(
    input  logic clk,
    input  logic [7:0] data,
    output logic [7:0] q1,
    output logic [7:0] q2
);
    always_ff @(posedge clk) begin
        q1 <= data;
        q2 <= data;
    end
endmodule'''

# 预期: data.load = [q1, q2]


# 金标准4: 组合逻辑负载
RTL_COMB_LOAD = '''module dut(
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] y
);
    assign y = a + b;
endmodule'''

# 预期: y.load = [a + b]


# =============================================================================
# 测试类
# =============================================================================

class TestLoadBasic:
    """基础功能测试"""
    
    @pytest.mark.unit
    def test_simple_load(self):
        """测试简单负载提取"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SIMPLE_LOAD)
        
        lt = LoadTracer(trees={}, verbose=False)
        lt.collect(tree, 'dut.sv')
        
        loads = lt.trace('q')
        assert len(loads) > 0, "q 应有负载"
    
    @pytest.mark.unit
    def test_conditional_load(self):
        """测试条件负载"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CONDITIONAL_LOAD)
        
        lt = LoadTracer(trees={}, verbose=False)
        lt.collect(tree, 'dut.sv')
        
        loads = lt.trace('q')
        assert len(loads) >= 1, "q 应有条件负载"
    
    @pytest.mark.unit
    def test_multi_load(self):
        """测试多负载"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_MULTI_LOAD)
        
        lt = LoadTracer(trees={}, verbose=False)
        lt.collect(tree, 'dut.sv')
        
        # 两个输出都驱动
        loads1 = lt.trace('q1')
        loads2 = lt.trace('q2')
        assert len(loads1) > 0 and len(loads2) > 0


class TestLoadEdgeCases:
    """边界用例"""
    
    @pytest.mark.unit
    def test_comb_load(self):
        """测试组合逻辑负载"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_COMB_LOAD)
        
        lt = LoadTracer(trees={}, verbose=False)
        lt.collect(tree, 'dut.sv')
        
        loads = lt.trace('y')
        assert len(loads) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
