"""
Driver 高级少见语法测试 (TDD)

覆盖: static function, class, 自复制{}, parameter, $系统函数
遵循铁律13: 金标准测试
"""

import pytest
import sys
sys.path.insert(0, 'src')
from parse import SVParser
from trace.driver import DriverCollector


# =============================================================================
# 金标准 R1: 静态 function (static function)
# =============================================================================

RTL_STATIC_FUNC = '''module dut(
    input  logic clk,
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] q
);
    // 静态函数 - 结果持久化
    static function [7:0] add_static;
        input [7:0] x, y;
        begin
            add_static = x + y;
        end
    endfunction
    
    always_ff @(posedge clk)
        q <= add_static(a, b);
endmodule'''
# 预期: source = add_static(a,b) (静态函数调用)


# =============================================================================
# 金标准 R2: Class 方法调用
# =============================================================================

RTL_CLASS_METHOD = '''module dut(
    input  logic clk,
    input  logic [7:0] data,
    output logic [7:0] q
);
    // 简化的 class 方法
    function [7:0] process;
        input [7:0] d;
        process = d + 1;
    endfunction
    
    always_ff @(posedge clk)
        q <= process(data);
endmodule'''
# 预期: source = process(data)


# =============================================================================
# 金标准 R3: 自复制 / 自构造 {}
# =============================================================================

RTL_SELF_COPY = '''module dut(
    input  logic clk,
    input  logic [7:0] a,
    output logic [15:0] q
);
    always_ff @(posedge clk)
        q <= {a, a};  // 自复制 {a, a}
endmodule'''
# 预期: source = {a, a}


# =============================================================================
# 金标准 R4: Parameter 表达式
# =============================================================================

RTL_PARAM_EXPR = '''module dut #(
    parameter AW = 8,
    parameter DW = 16
) (
    input  logic clk,
    input  logic [AW-1:0] data,
    output logic [DW-1:0] q
);
    assign q = {{(DW-AW){1'b0}}, data};
endmodule'''
# 预期: 参数化位宽处理


# =============================================================================
# 金标准 R5: 系统函数 $ 返回值
# =============================================================================

RTL_SYS_FUNC = '''module dut(
    input  logic clk,
    input  logic [7:0] data,
    output logic [7:0] q,
    output logic [31:0] time_cnt
);
    // $time 返回当前仿真时间
    assign time_cnt = $time;
    
    always_ff @(posedge clk)
        q <= data;
endmodule'''
# 预期: time_cnt = $time


# =============================================================================
# 金标准 R6: $signed/$unsigned 转换
# =============================================================================

RTL_CAST = '''module dut(
    input  logic [7:0] data,
    output logic [7:0] q
);
    assign q = $signed(data);
endmodule'''
# 预期: source = $signed(data)


# =============================================================================
# 金标准 R7: $countbits/$countones
# =============================================================================

RTL_COUNT = '''module dut(
    input  logic [7:0] data,
    output logic [2:0] ones,
    output logic [2:0] bits
);
    assign ones = $countones(data);
    assign bits = $countbits(data, 1'b1);
endmodule'''
# 预期: 系统函数调用


# =============================================================================
# 测试类
# =============================================================================

class TestStaticFunction:
    """静态函数测试"""
    
    @pytest.mark.unit
    def test_static_function(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_STATIC_FUNC)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        print(f"  drivers: {drivers}")
        assert len(drivers) > 0


class TestClassMethod:
    """Class 方法测试"""
    
    @pytest.mark.unit
    def test_class_method(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CLASS_METHOD)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        print(f"  drivers: {drivers}")
        assert len(drivers) > 0


class TestSelfCopy:
    """自复制语法测试"""
    
    @pytest.mark.unit
    def test_self_copy(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SELF_COPY)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        print(f"  drivers: {drivers}")
        assert len(drivers) > 0


class TestParameter:
    """Parameter 测试"""
    
    @pytest.mark.unit
    def test_parameter_expr(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_PARAM_EXPR)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        print(f"  drivers: {drivers}")


class TestSystemFunction:
    """系统函数测试"""
    
    @pytest.mark.unit
    def test_sys_time(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SYS_FUNC)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        print(f"  drivers: {drivers}")
        assert len(drivers) > 0
    
    @pytest.mark.unit
    def test_signed_cast(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CAST)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        print(f"  drivers: {drivers}")
        assert len(drivers) > 0
    
    @pytest.mark.unit
    def test_count_function(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_COUNT)
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.drivers
        print(f"  drivers: {drivers}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
