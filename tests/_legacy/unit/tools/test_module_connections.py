"""
Module Connections 工具测试 (TDD)

遵循铁律13: 金标准测试
- 先推导金标准，再对比验证

目标: 验证模块实例和端口连接关系的提取
"""

import pytest
import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.connection import ConnectionTracer


# =============================================================================
# 金标准用例 (Golden Standard)
# =============================================================================

# 金标准1: 简单模块实例连接
RTL_SIMPLE_INSTANCE = '''module dut(input clk, input d, output q);
    sub u_sub(.clk(clk), .d(d), .q(q));
endmodule

module sub(
    input  logic clk,
    input  logic d,
    output logic q
);
    always_ff @(posedge clk) q <= d;
endmodule'''

# 金标准2: 层次化连接
RTL_HIERARCHY = '''module top(input clk, input [7:0] data, output [7:0] out);
    sub1 u_s1(.clk(clk), .din(data[3:0]), .dout(out[3:0]));
    sub2 u_s2(.clk(clk), .din(data[7:4]), .dout(out[7:4]));
endmodule

module sub1(input clk, input [3:0] din, output [3:0] dout);
    always_ff @(posedge clk) dout <= din;
endmodule

module sub2(input clk, input [3:0] din, output [3:0] dout);
    always_ff @(posedge clk) dout <= din;
endmodule'''

# 金标准3: 跨模块信号传递
RTL_CROSS_MODULE = '''module a(input clk, input d, output q);
    b u_b(.clk(clk), .din(d), .dout(q));
endmodule

module b(input clk, input din, output q);
    always_ff @(posedge clk) q <= din;
endmodule'''


# =============================================================================
# 测试类
# =============================================================================

class TestBasic:
    """基础连接测试"""
    
    @pytest.mark.unit
    def test_simple_instance(self):
        """测试简单模块实例提取"""
        # 金标准推导:
        # - 模块 dut 实例化 sub，实例名 u_sub
        # - 连接关系: clk->clk, d->d, q->q
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SIMPLE_INSTANCE)
        
        ct = ConnectionTracer(verbose=False)
        ct.collect(tree, 'dut.sv')
        
        # 验证实例存在
        assert len(ct.instances) >= 1, "应有模块实例"
        instance_names = [i.name for i in ct.instances]
        assert 'u_sub' in instance_names, "实例名应为 u_sub"
        
        # 验证连接关系
        assert len(ct.connections) >= 1, "应有连接关系"
    
    @pytest.mark.unit
    def test_hierarchy(self):
        """测试层次化模块实例"""
        # 金标准推导:
        # - top 实例化 sub1 (u_s1) 和 sub2 (u_s2)
        # - 2个实例，4个连接 (每个子模块2个端口)
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_HIERARCHY)
        
        ct = ConnectionTracer(verbose=False)
        ct.collect(tree, 'top.sv')
        
        # 验证实例数量
        assert len(ct.instances) >= 2, f"应有2个实例，实际: {len(ct.instances)}"
        instance_names = [i.name for i in ct.instances]
        assert 'u_s1' in instance_names, "应有 u_s1"
        assert 'u_s2' in instance_names, "应有 u_s2"
    
    @pytest.mark.unit
    def test_cross_module(self):
        """测试跨模块连接"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CROSS_MODULE)
        
        ct = ConnectionTracer(verbose=False)
        ct.collect(tree, 'a.sv')
        
        # 验证实例存在
        assert len(ct.instances) >= 1, "应有模块实例"
        instance_names = [i.name for i in ct.instances]
        assert 'u_b' in instance_names, "实例名应为 u_b"


class TestConnectionProperties:
    """连接属性测试"""
    
    @pytest.mark.unit
    def test_connection_has_signal(self):
        """验证连接包含信号信息"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SIMPLE_INSTANCE)
        
        ct = ConnectionTracer(verbose=False)
        ct.collect(tree, 'dut.sv')
        
        # 每个连接应该有 source/dest
        for conn in ct.connections:
            assert conn.source or conn.dest, f"连接应有信号: {conn}"


class TestEdgeCases:
    """边界用例"""
    
    @pytest.mark.unit
    def test_no_instance(self):
        """测试无模块实例的RTL"""
        rtl = '''module single(input clk, d, output q);
            always_ff @(posedge clk) q <= d;
        endmodule'''
        
        parser = SVParser(verbose=False)
        tree = parser.parse_text(rtl)
        
        ct = ConnectionTracer(verbose=False)
        ct.collect(tree, 'single.sv')
        
        # 单模块无实例
        assert len(ct.instances) == 0, "单模块不应有实例"


# =============================================================================
# 主入口
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])