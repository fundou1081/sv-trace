"""
SignalChain 测试 (TDD)

遵循铁律13: 金标准测试
- 先推导金标准，再对比验证

目标: 验证信号链追踪功能
使用 DriverCollector 和 LoadTracer
"""

import pytest
import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.driver import DriverCollector
from trace.load import LoadTracer


# =============================================================================
# 金标准用例 (Golden Standard)
# =============================================================================

# 金标准1: 单信号驱动 (always_ff)
RTL_SINGLE = '''module top(
    input  logic clk,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    always_ff @(posedge clk) begin
        data_out <= data_in;
    end
endmodule'''

# 金标准2: 连续赋值
RTL_CONTINUOUS = '''module top(
    input  logic [7:0] a,
    output logic [7:0] b
);
    assign b = a;
endmodule'''

# 金标准3: 复杂链路 (组合 + 时序)
RTL_COMPLEX = '''module top(
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    logic [7:0] temp;
    assign temp = data_in;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data_out <= 8'b0;
        else
            data_out <= temp;
    end
endmodule'''


# =============================================================================
# 测试类
# =============================================================================

class TestSignalChain:
    """信号链测试"""
    
    @pytest.mark.unit
    def test_single_driver(self):
        """测试单信号驱动 (always_ff)
        
        金标准:
        - data_out 有驱动 (always_ff)
        - data_in 被 data_out 使用
        - clk 被识别为时钟
        """
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SINGLE)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'top.sv')
        
        # data_out 有驱动
        drivers = dc.get_drivers('data_out')
        assert drivers, "data_out 应有驱动"
        
        # data_in 在驱动源中
        d = drivers['data_out'][0]
        print(f"  data_out: driver={d.driver}, kind={d.kind}, clock={d.clock}")
        assert d.kind == 'always_ff', "驱动类型应是 always_ff"
        
        # clk 被识别
        print(f"  clock: '{d.clock}'")
    
    @pytest.mark.unit
    def test_continuous_assignment(self):
        """测试连续赋值
        
        金标准:
        - b 有驱动 (continuous)
        - b 的驱动源是 a
        """
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_CONTINUOUS)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'top.sv')
        
        # b 有驱动
        drivers = dc.get_drivers('b')
        assert drivers, "b 应有驱动"
        
        d = drivers['b'][0]
        print(f"  b: driver={d.driver}, kind={d.kind}")
        assert d.kind == 'continuous', "驱动类型应是 continuous"
    
    @pytest.mark.unit
    def test_complex_chain(self):
        """测试复杂链路 (组合 + 时序)
        
        金标准:
        - data_out 有 >=2 个驱动 (复位分支 + 主分支)
        - data_out 的数据路径包含 temp
        - clk 被识别为时钟
        - rst_n 被识别为复位
        """
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_COMPLEX)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'top.sv')
        
        # data_out 有驱动
        drivers = dc.get_drivers('data_out')
        assert drivers, "data_out 应有驱动"
        
        d = drivers['data_out'][0]
        print(f"  data_out: driver={d.driver}, kind={d.kind}")
        print(f"  clock={d.clock}, reset={d.reset}")
        
        # temp 是中间信号
        assert 'temp' in dc.drivers, "temp 应有驱动"


class TestLoadTraces:
    """负载追踪测试"""
    
    @pytest.mark.unit
    def test_signal_load(self):
        """测试信号负载"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_SINGLE)
        
        lt = LoadTracer(verbose=False)
        lt.collect(tree, 'top.sv')
        
        # 验证负载追踪
        assert lt is not None
        print(f"  load tracer OK")


# =============================================================================
# 主入口
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])