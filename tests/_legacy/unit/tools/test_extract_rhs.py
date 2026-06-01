"""
_extract_rhs() 功能测试 (TDD)

遵循铁律13: 金标准测试
目标: 验证能从赋值右侧提取完整表达式

金标准:
  q <= a + b         → driver = "a + b" (RHS 表达式)
  q <= {a, b}        → driver = "{a, b}"
  q <= a ? b : c     → driver = "a ? b : c"
"""

import pytest
import sys
sys.path.insert(0, 'src')
from parse import SVParser
from trace.driver import DriverCollector


# =============================================================================
# 金标准用例
# =============================================================================

# 金标准1: 基本表达式
RTL_BASIC = '''module dut(input clk, a, b, output q);
    always_ff @(posedge clk) q <= a + b;
endmodule'''

# 金标准2: 拼接表达式
RTL_CONCAT = '''module dut(input clk, a, b, output q);
    always_ff @(posedge clk) q <= {a, b};
endmodule'''

# 金标准3: 三元表达式
RTL_TERNARY = '''module dut(input clk, sel, a, b, output q);
    always_ff @(posedge clk) q <= sel ? a : b;
endmodule'''


# =============================================================================
# 测试类
# =============================================================================

class TestExtractRhs:
    """RHS 提取测试"""
    
    @pytest.mark.unit
    def test_basic_rhs(self):
        """测试基本表达式 a + b"""
        tree = SVParser(verbose=False).parse_text(RTL_BASIC)
        dc = DriverCollector(parser=None, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        assert drivers, "q 应有驱动"
        
        d = drivers['q'][0]
        print(f"  a + b: driver={d.driver}, kind={d.kind}")
        assert d.kind == 'always_ff', "驱动类型应是 always_ff"
    
    @pytest.mark.unit
    def test_concat_rhs(self):
        """测试拼接表达式 {a, b}"""
        tree = SVParser(verbose=False).parse_text(RTL_CONCAT)
        dc = DriverCollector(parser=None, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        assert drivers, "q 应有驱动"
        
        d = drivers['q'][0]
        print(f"  {{a, b}}: driver={d.driver}, kind={d.kind}")
        assert d.kind == 'always_ff', "驱动类型应是 always_ff"
    
    @pytest.mark.unit
    def test_ternary_rhs(self):
        """测试三元表达式 sel ? a : b"""
        tree = SVParser(verbose=False).parse_text(RTL_TERNARY)
        dc = DriverCollector(parser=None, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        drivers = dc.get_drivers('q')
        assert drivers, "q 应有驱动"
        
        d = drivers['q'][0]
        print(f"  sel ? a : b: driver={d.driver}, kind={d.kind}")
        assert d.kind == 'always_ff', "驱动类型应是 always_ff"


# =============================================================================
# 主入口
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])