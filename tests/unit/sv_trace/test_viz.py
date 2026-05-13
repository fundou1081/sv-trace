"""
Visualization 工具测试 (TDD)

遵循铁律13: 金标准测试
- 先推导金标准，再对比验证

目标: 验证数据流和控制流的可视化追踪
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

# 金标准1: 简单流水线数据流
# din → s1 → s2 → dout
RTL_PIPELINE = '''module pipe(
    input  logic clk,
    input  logic [31:0] din,
    output logic [31:0] dout
);
    logic [31:0] s1, s2;
    always_ff @(posedge clk) begin
        s1 <= din;
        s2 <= s1;
        dout <= s2;
    end
endmodule'''

# 金标准2: FSM 控制流
RTL_FSM = '''module fsm(
    input  logic clk,
    input  logic req,
    output logic ack
);
    logic [1:0] state;
    always_ff @(posedge clk) begin
        case(state)
            2'b00: state <= req ? 2'b01 : 2'b00;
            2'b01: state <= ack ? 2'b00 : 2'b01;
            default: state <= 2'b00;
        endcase
    end
endmodule'''


# =============================================================================
# 测试类
# =============================================================================

class TestDatapathViz:
    """数据流可视化测试"""
    
    @pytest.mark.unit
    def test_pipeline_datapath_drivers(self):
        """测试流水线数据流驱动关系"""
        # 金标准推导:
        # - din 驱动 s1 (s1 <= din)
        # - s1 驱动 s2 (s2 <= s1)
        # - s2 驱动 dout (dout <= s2)
        # - 3个寄存器阶段
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_PIPELINE)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'pipe.sv')
        
        # 验证数据流节点
        assert 's1' in dc.drivers, "应有 s1 驱动"
        assert 's2' in dc.drivers, "应有 s2 驱动"
        assert 'dout' in dc.drivers, "应有 dout 驱动"
        
        # 验证阶段数量
        register_count = sum(1 for sig in dc.drivers if sig in ('s1', 's2', 'dout'))
        assert register_count == 3, f"应有3个寄存器，实际: {register_count}"
    
    @pytest.mark.unit
    def test_fsm_controlflow_drivers(self):
        """测试 FSM 控制流驱动关系"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_FSM)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'fsm.sv')
        
        # 验证控制流
        assert 'state' in dc.drivers, "应有 state 驱动"


class TestDotFormatOutput:
    """DOT 格式输出测试"""
    
    @pytest.mark.unit
    def test_generate_dot_nodes(self):
        """测试生成 DOT 格式的节点"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_PIPELINE)
        
        dc = DriverCollector(parser=parser, verbose=False)
        dc.collect(tree, 'pipe.sv')
        
        # 生成节点列表
        nodes = list(dc.drivers.keys())
        
        # DOT 格式
        dot_lines = [f"    {sig};" for sig in nodes if sig in ('s1', 's2', 'dout')]
        
        dot = f"digraph datapath {{\n"
        dot += "    // Pipeline registers\n"
        dot += "\n".join(dot_lines)
        dot += "\n}"
        
        print(f"\nDOT format:\n{dot}")
        assert len(dot_lines) == 3, "应有3个节点"


class TestLoadTraces:
    """负载追踪测试"""
    
    @pytest.mark.unit
    def test_signal_load_chain(self):
        """测试信号负载链"""
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_PIPELINE)
        
        lt = LoadTracer(verbose=False)
        lt.collect(tree, 'pipe.sv')
        
        # 验证负载追踪
        assert lt is not None
        # 基本验证 - 不崩溃


# =============================================================================
# 主入口
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])