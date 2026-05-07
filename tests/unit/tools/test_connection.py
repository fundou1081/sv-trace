"""
Connection 工具测试 (TDD 方式)

遵循铁律13: 金标准测试
目标: src/trace/connection.py
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from parse import SVParser
from trace.connection import ConnectionTracer


# =============================================================================
# 金标准用例
# =============================================================================

# 金标准1: 简单实例连接
RTL_SIMPLE_INST = '''module dut(
    input clk,
    input [7:0] data,
    output [7:0] q
);
    sub u_sub(.clk(clk), .din(data), .dout(q));
endmodule

module sub(
    input clk,
    input [7:0] din,
    output [7:0] dout
);
    always_ff @(posedge clk) dout <= din;
endmodule'''

# 预期: top → sub 实例连接


# 金标准2: 多层连接
RTL_HIERARCHY = '''module top(
    input clk,
    input [7:0] din,
    output [7:0] dout
);
    level1 u_l1(.clk(clk), .din(din));
endmodule

module level1(
    input clk,
    input [7:0] din,
    output [7:0] dout
);
    level2 u_l2(.clk(clk), .din(din), .dout(dout));
endmodule

module level2(
    input clk,
    input [7:0] din,
    output [7:0] dout
);
    always_ff @(posedge clk) dout <= din;
endmodule'''

# 预期: 3层层次


# 金标准3: 跨模块连接
RTL_CROSS_MODULE = '''module a(
    input clk,
    output [7:0] dout
);
    assign dout = 8'hAA;
endmodule

module b(
    input [7:0] din,
    output [7:0] dout
);
    assign dout = din;
endmodule

module top(
    input clk,
    output [7:0] q
);
    a u_a(.clk(clk), .dout(din));
    b u_b(.din(din), .dout(q));
endmodule'''

# 预期: 模块间连接链


# =============================================================================
# 测试类
# =============================================================================

class TestConnectionBasic:
    """基础功能测试"""
    
    @pytest.mark.unit
    def test_simple_instance(self):
        """测试简单实例连接"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SIMPLE_INST)
        
        ct = ConnectionTracer(trees={}, verbose=False)
        ct.collect(tree, 'dut.sv')
        
        instances = ct.all_instances
        assert len(instances) > 0, "应有实例"
    
    @pytest.mark.unit
    def test_hierarchy(self):
        """测试层次连接"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_HIERARCHY)
        
        ct = ConnectionTracer(trees={}, verbose=False)
        ct.collect(tree, 'top.sv')
        
        instances = ct.all_instances
        assert len(instances) >= 2, "应有3层实例"
    
    @pytest.mark.unit
    def test_cross_module(self):
        """测试跨模块连接"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CROSS_MODULE)
        
        ct = ConnectionTracer(trees={}, verbose=False)
        ct.collect(tree, 'top.sv')
        
        instances = ct.all_instances
        assert len(instances) >= 2, "应有多个模块"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
