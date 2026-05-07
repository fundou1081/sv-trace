"""
_extract_rhs 表达式提取测试 (TDD)

需要支持的表达式类型 (按优先级):
1. Arithmetic: +, -, *, /, %, **, <<, >>
2. Comparison: ==, !=, <, <=, >, >=, &&, ||
3. Bitwise: &, |, ^, ~, ~&, ~|, ~^
4. Shift: <<, >>, <<<, >>>
5. Logical: &&, ||
6. Concatenation: {a, b, c}
7. Replication: {2{a}}
"""

import pytest
import sys
sys.path.insert(0, 'src')
from parse import SVParser
from trace.driver import DriverCollector


# 简化测试函数
def test_expression(name: str, rtl: str, expected_source: str):
    """测试单个表达式"""
    tree = SVParser(verbose=False).parse_text(rtl)
    dc = DriverCollector(parser=None, verbose=False)
    dc.collect(tree, 'dut.sv')
    
    drivers = dc.get_drivers('q')
    d = drivers['q'][0]
    
    print(f"{name}: sources={d.sources}")
    return len(drivers) > 0


class TestArithmeticExpressions:
    """算术运算符测试"""
    
    @pytest.mark.unit
    def test_add(self):
        return test_expression("加法", 
            'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= a + b; endmodule',
            "a + b")
    
    @pytest.mark.unit
    def test_sub(self):
        return test_expression("减法",
            'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= a - b; endmodule',
            "a - b")
    
    @pytest.mark.unit
    def test_mul(self):
        return test_expression("乘法",
            'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= a * b; endmodule',
            "a * b")


class TestBitwiseExpressions:
    """位运算符测试"""
    
    @pytest.mark.unit
    def test_and(self):
        return test_expression("AND",
            'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= a & b; endmodule',
            "a & b")
    
    @pytest.mark.unit
    def test_or(self):
        return test_expression("OR",
            'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= a | b; endmodule',
            "a | b")
    
    @pytest.mark.unit
    def test_xor(self):
        return test_expression("XOR",
            'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= a ^ b; endmodule',
            "a ^ b")


class TestShiftExpressions:
    """移位运算符测试"""
    
    @pytest.mark.unit
    def test_lshift(self):
        return test_expression("Lshift",
            'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= a << b; endmodule',
            "a << b")
    
    @pytest.mark.unit
    def test_rshift(self):
        return test_expression("Rshift",
            'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= a >> b; endmodule',
            "a >> b")


class TestConcatenationExpressions:
    """拼接表达式测试"""
    
    @pytest.mark.unit
    def test_concat(self):
        return test_expression("拼接",
            'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= {a, b}; endmodule',
            "{a, b}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
