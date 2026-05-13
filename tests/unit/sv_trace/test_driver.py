"""
Driver 测试 (TDD)

遵循铁律13: 金标准测试
目标: 验证 DriverCollector 功能
"""

import pytest
import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.driver import DriverCollector


# =============================================================================
# 金标准用例 (Golden Standard)
# =============================================================================

# 金标准1: 简单加法赋值
TEST_SIMPLE = '''module t(
    input  logic [31:0] a,
    input  logic [31:0] b,
    output logic [31:0] r
);
    always_comb r = a + b;
endmodule'''

# 金标准2: 多路选择
TEST_NESTED = '''module t(
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [31:0] c,
    input  logic [1:0] sel,
    output logic [31:0] r
);
    always_comb begin
        if (sel == 2'b00)
            r = a;
        else if (sel == 2'b01)
            r = b;
        else
            r = c;
    end
endmodule'''


# =============================================================================
# 测试函数
# =============================================================================

@pytest.mark.unit
def test_simple():
    """简单赋值测试"""
    parser = SVParser(verbose=False)
    tree = parser.parse_text(TEST_SIMPLE)
    
    dc = DriverCollector(parser=parser, verbose=False)
    dc.collect(tree, 't.sv')
    
    # r 有驱动
    drivers = dc.get_drivers('r')
    assert drivers, "r 应有驱动"
    
    d = drivers['r'][0]
    print(f"  r: kind={d.kind}, driver={d.driver}")
    assert d.kind == 'always_comb', "驱动类型应是 always_comb"


@pytest.mark.unit
def test_nested():
    """嵌套 if 测试"""
    parser = SVParser(verbose=False)
    tree = parser.parse_text(TEST_NESTED)
    
    dc = DriverCollector(parser=parser, verbose=False)
    dc.collect(tree, 't.sv')
    
    # r 有驱动
    drivers = dc.get_drivers('r')
    assert drivers, "r 应有驱动"
    
    d = drivers['r'][0]
    print(f"  r: kind={d.kind}, driver={d.driver}")
    assert d.kind == 'always_comb', "驱动类型应是 always_comb"


# =============================================================================
# 主入口
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])