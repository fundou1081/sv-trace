"""
Controlflow 工具测试 (TDD)
目标: 验证控制流分析功能

遵循铁律13: 金标准测试
- 先推导金标准，再对比验证
"""

import pytest
import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.driver import DriverCollector
from trace.connection import ConnectionTracer


# =============================================================================
# 金标准用例 (Golden Standard)
# =============================================================================

# 金标准1: if-else 控制流
# y 被条件 a 控制
RTL_IF = '''module dut(input logic a, output logic y);
    always_comb if (a) y = 1; else y = 0;
endmodule'''

# 金标准2: case 语句
# y 被 sel 控制
RTL_CASE = '''module dut(input [1:0] sel, output logic y);
    always_comb case (sel)
        2'd0: y = 1;
        2'd1: y = 2;
        default: y = 0;
    endcase
endmodule'''

# 金标准3: for 循环
# cnt 在时钟下被更新
RTL_FOR = '''module dut(input clk, output logic [7:0] y);
    logic [7:0] cnt;
    always_ff @(posedge clk) begin
        for (int i=0; i<8; i++) cnt[i] <= 1'b0;
        y <= cnt;
    end
endmodule'''


# =============================================================================
# 测试类
# =============================================================================

class TestControlFlowBasic:
    @pytest.mark.unit
    def test_if_else(self):
        """测试 if-else 控制流"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_IF)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        # 金标准: y 应该有驱动
        assert 'y' in dc.drivers, "y 应有驱动"
        
        y_drivers = dc.get_drivers('y')
        print(f"  y drivers: {len(y_drivers.get('y', []))}")
    
    @pytest.mark.unit
    def test_case(self):
        """测试 case 语句控制流"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CASE)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        # 金标准: y 应该有驱动
        assert 'y' in dc.drivers, "y 应有驱动"
        
        y_drivers = dc.get_drivers('y')
        print(f"  y drivers: {len(y_drivers.get('y', []))}")
    
    @pytest.mark.unit
    def test_for_loop(self):
        """测试 for 循环"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_FOR)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        # 金标准: cnt 和 y 都应该有驱动
        assert 'cnt' in dc.drivers, "cnt 应有驱动"
        assert 'y' in dc.drivers, "y 应有驱动"
        
        print(f"  drivers: {list(dc.drivers.keys())}")


# =============================================================================
# 主入口
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])