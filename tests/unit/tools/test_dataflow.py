"""
Dataflow 工具测试 (TDD 方式)

遵循铁律13: 金标准测试
目标: 验证数据流分析功能
"""

import pytest
import sys
import os
sys.path.insert(0, 'src')

from parse import SVParser
from trace.driver import DriverCollector


# =============================================================================
# 金标准用例
# =============================================================================

# 金标准1: 简单模块 - 1个寄存器
RTL_SIMPLE = '''module dut(
    input  logic clk,
    input  logic [7:0] data,
    output logic [7:0] q
);
    always_ff @(posedge clk) q <= data;
endmodule'''

# 金标准2: 多寄存器流水线
RTL_PIPELINE = '''module dut(
    input  logic clk,
    input  logic [7:0] data,
    output logic [7:0] q
);
    logic [7:0] s1, s2;
    always_ff @(posedge clk) begin
        s1 <= data;
        s2 <= s1;
        q <= s2;
    end
endmodule'''


# =============================================================================
# 测试类
# =============================================================================

class TestDataFlowBasic:
    """基础功能测试"""
    
    @pytest.mark.unit
    def test_collect(self):
        """测试数据流收集"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SIMPLE)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        # 可收集即可
        assert dc is not None
        assert len(dc.drivers) >= 1, "应有驱动关系"
    
    @pytest.mark.unit
    def test_register_count(self):
        """测试寄存器计数"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SIMPLE)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        # q 是寄存器 (always_ff 驱动)
        assert 'q' in dc.drivers, "q 应有驱动"
        
        q_drivers = dc.get_drivers('q')
        d = q_drivers['q'][0]
        assert d.kind == 'always_ff', "q 应该是 always_ff 驱动"
        print(f"  q kind: {d.kind}")
    
    @pytest.mark.unit
    def test_wire_count(self):
        """测试线网计数"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SIMPLE)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        # 验证驱动数量
        assert len(dc.drivers) >= 1
        print(f"  signals: {list(dc.drivers.keys())}")


class TestDataFlowPipeline:
    """流水线测试"""
    
    @pytest.mark.unit
    def test_pipeline_stages(self):
        """测试流水线阶段"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_PIPELINE)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'dut.sv')
        
        # 3个寄存器: s1, s2, q
        for sig in ['s1', 's2', 'q']:
            assert sig in dc.drivers, f"{sig} 应有驱动"
        
        print(f"  pipeline signals: {list(dc.drivers.keys())}")


# =============================================================================
# 主入口
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])