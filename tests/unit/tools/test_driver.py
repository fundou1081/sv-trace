"""
Driver 工具测试 (TDD 方式)

遵循铁律13: 金标准测试
- 先推导金标准，再对比验证

目标: src/trace/driver.py
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

# 使用 SVParser
from parse import SVParser
from trace.driver import DriverCollector


# =============================================================================
# 金标准用例 (Golden Standard)
# =============================================================================

# 金标准1: 简单 always_ff 驱动
RTL_ALWAYS_FF = '''module dut(
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) data_out <= 8'h00;
        else       data_out <= data_in;
    end
endmodule'''

# 金标准2: always_comb 驱动
RTL_ALWAYS_COMB = '''module dut(
    input  logic clk_en,
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] y
);
    always_comb begin
        if (clk_en) y = a;
        else     y = b;
    end
endmodule'''

# 金标准3: 连续赋值
RTL_CONTINUOUS_ASSIGN = '''module dut(
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] y
);
    assign y = a & b;
endmodule'''

# 金标准4: 派生时钟
RTL_DERIVED_CLOCK = '''module dut(
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] data,
    output logic [7:0] q
);
    logic clk_div2;
    assign clk_div2 = clk;
    
    always_ff @(posedge clk_div2 or negedge rst_n) begin
        if (!rst_n) q <= 8'h00;
        else       q <= data;
    end
endmodule'''


# =============================================================================
# 测试类
# =============================================================================

class TestDriverBasic:
    """基础功能测试"""
    
    @pytest.mark.unit
    def test_always_ff_driver(self):
        """测试 always_ff 驱动提取"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_ALWAYS_FF)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('data_out')
        assert len(drivers) > 0, "data_out 应有驱动"
    
    @pytest.mark.unit
    def test_always_comb_driver(self):
        """测试 always_comb 驱动提取"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_ALWAYS_COMB)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('y')
        assert len(drivers) > 0, "y 应有驱动"
    
    @pytest.mark.unit
    def test_continuous_assign(self):
        """测试连续赋值驱动"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CONTINUOUS_ASSIGN)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('y')
        assert len(drivers) > 0, "连续赋值应有驱动"


class TestDriverEdgeCases:
    """边界用例测试"""
    
    @pytest.mark.unit
    def test_no_clock(self):
        """测试无时钟的组合逻辑"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_ALWAYS_COMB)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        clocks = dc.all_clocks
        assert len(clocks) == 0, "组合逻辑应无时钟"
    
    @pytest.mark.unit
    def test_derived_clock(self):
        """测试派生时钟"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_DERIVED_CLOCK)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        assert len(dc.all_clocks) >= 1


class TestDriverIntegration:
    """集成测试"""
    
    @pytest.mark.integration
    def test_opentitan_module(self):
        """测试 OpenTitan 模块"""
        pytest.skip("需要 OpenTitan 项目文件")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
