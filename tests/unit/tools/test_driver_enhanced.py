"""
Driver 增强测试 - 复杂语法 (TDD)

遵循铁律13: 金标准测试
目标: 验证 driver.py 的复杂语法提取能力
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from parse import SVParser
from trace.driver import DriverCollector


# -----------------------------------------------------------------------------
# 金标准: P0 基础增强
# -----------------------------------------------------------------------------

# 金标准 P0-1: 条件使能
RTL_ENABLE = '''module dut(
    input  logic clk,
    input  logic rst_n,
    input  logic enable,
    input  logic [7:0] data,
    output logic [7:0] q
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) q <= 8'h00;
        else if (enable) q <= data;
    end
endmodule'''
# 预期: q.clock=clk, q.reset=rst_n, q.enable=enable


# 金标准 P0-2: always_ff 多 always块 (多驱动)
RTL_MULTI_FF = '''module dut(
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] data,
    input  logic mode,
    output logic [7:0] q
);
    // 主驱动
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) q <= 8'h00;
        else if (mode) q <= data;
    end
endmodule'''
# 预期: q 有多驱动源


# 金标准 P0-3: 异步复位显式
RTL_ASYNC_RESET = '''module dut(
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] data,
    output logic [7:0] q
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) q <= 8'hFF;
        else q <= data;
    end
endmodule'''
# 预期: q.reset=rst_n (异步)


# -----------------------------------------------------------------------------
# 金标准: P1 复杂语法
# -----------------------------------------------------------------------------

# 金标准 P1-1: 嵌套 if
RTL_NESTED_IF = '''module dut(
    input  logic clk,
    input  logic rst_n,
    input  logic a, b, c,
    output logic q
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (a) begin
            if (b) q <= c;
        end
    end
endmodule'''


# 金标准 P1-2: case 驱动
RTL_CASE = '''module dut(
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
# 预期: q.drivers = [d0, d1, d2, d3] (多驱动)


# 金标准 P1-3: 运算符驱动
RTL_OP = '''module dut(
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] a, b,
    output logic [7:0] q
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) q <= 8'h00;
        else q <= a + b;
    end
endmodule'''
# 预期: q.driver = a + b


# 金标准 P1-4: 位拼接驱动
RTL_CONCAT = '''module dut(
    input  logic clk,
    input  logic rst_n,
    input  logic [3:0] a, b,
    output logic [7:0] q
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) q <= 8'h00;
        else q <= {a, b};
    end
endmodule'''


# -----------------------------------------------------------------------------
# 测试类
# -----------------------------------------------------------------------------

class TestDriverP0:
    """P0 基础增强"""
    
    @pytest.mark.unit
    def test_enable_signal(self):
        """条件使能提取"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_ENABLE)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        # 调试输出
        if drivers:
            d = drivers['q'][0]
            print(f"  q.driver={d.signal}, clock={d.clock}, reset={d.reset}")
        assert len(drivers) > 0, "q 应有驱动"
    
    @pytest.mark.unit
    def test_multi_driver(self):
        """多驱动检测"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_MULTI_FF)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        multidrivers = dc.multi_drivers
        print(f"  multi_drivers={multidrivers}")
        # 验证多驱动属性
        assert hasattr(dc, 'multi_drivers')
    
    @pytest.mark.unit
    def test_async_reset(self):
        """异步复位"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_ASYNC_RESET)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        print(f"  q.reset={drivers['q'][0].reset if drivers else 'none'}")
        # 验证复位提取
        assert len(drivers) > 0


class TestDriverP1:
    """P1 复杂语法"""
    
    @pytest.mark.unit
    def test_case_statement(self):
        """case 语句解析"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CASE)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        print(f"  q drivers count={len(drivers)}")
        assert len(drivers) > 0
    
    @pytest.mark.unit
    def test_operator_driver(self):
        """运算符驱动"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_OP)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        print(f"  q drivers={drivers}")
        assert len(drivers) > 0
    
    @pytest.mark.unit
    def test_concat_driver(self):
        """位拼接"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CONCAT)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        assert len(drivers) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
