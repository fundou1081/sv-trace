"""
_extract_rhs 表达式提取测试 (TDD)

遵循铁律13: 金标准测试
- 先推导金标准，再对比验证

目标: 验证各种表达式类型的 RHS 提取
"""

import pytest
import sys
sys.path.insert(0, 'src')
from parse import SVParser
from trace.driver import DriverCollector


# =============================================================================
# 金标准用例 (Golden Standard)
# =============================================================================

RTL_BASE = 'module dut(input clk, a, b, output q); always_ff @(posedge clk) q <= {}; endmodule'


# =============================================================================
# 测试辅助函数
# =============================================================================

def _test_expr(name: str, expr: str):
    """测试单个表达式"""
    rtl = RTL_BASE.format(expr)
    tree = SVParser(verbose=False).parse_text(rtl)
    dc = DriverCollector(parser=None, verbose=False)
    dc.collect(tree, 'dut.sv')
    
    drivers = dc.get_drivers('q')
    if not drivers or 'q' not in drivers or not drivers['q']:
        print(f"  {name}: no drivers found")
        return False
    
    d = drivers['q'][0]
    print(f"  {name}: driver={d.driver}, kind={d.kind}")
    return True


# =============================================================================
# 测试类
# =============================================================================

class TestArithmeticExpressions:
    """算术运算符测试"""
    
    @pytest.mark.unit
    def test_add(self):
        """加法: a + b"""
        assert _test_expr("加法", "a + b")
    
    @pytest.mark.unit
    def test_sub(self):
        """减法: a - b"""
        assert _test_expr("减法", "a - b")
    
    @pytest.mark.unit
    def test_mul(self):
        """乘法: a * b"""
        assert _test_expr("乘法", "a * b")


class TestBitwiseExpressions:
    """位运算符测试"""
    
    @pytest.mark.unit
    def test_and(self):
        """AND: a & b"""
        assert _test_expr("AND", "a & b")
    
    @pytest.mark.unit
    def test_or(self):
        """OR: a | b"""
        assert _test_expr("OR", "a | b")
    
    @pytest.mark.unit
    def test_xor(self):
        """XOR: a ^ b"""
        assert _test_expr("XOR", "a ^ b")


class TestShiftExpressions:
    """移位运算符测试"""
    
    @pytest.mark.unit
    def test_lshift(self):
        """左移: a << b"""
        assert _test_expr("Lshift", "a << b")
    
    @pytest.mark.unit
    def test_rshift(self):
        """右移: a >> b"""
        assert _test_expr("Rshift", "a >> b")


class TestConcatenationExpressions:
    """拼接表达式测试"""
    
    @pytest.mark.unit
    def test_concat(self):
        """拼接: {a, b}"""
        assert _test_expr("拼接", "{a, b}")


# =============================================================================
# 主入口
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])