"""Driver 语义验证测试

深入验证提取结果与语义一致性
符合铁律 4: 模型即契约
"""

import pytest
import sys
sys.path.insert(0, 'src')

from sv_manager import SVManager
from trace.driver import DriverCollector
from semantic.base import SemanticCollector
from semantic.driver import NonBlockingAssign, DriverSignal


class TestDriverSemanticValidation:
    """语义验证测试"""
    
    @pytest.fixture
    def parser(self):
        return SVManager()
    
    def test_basic_ff_signal_name(self, parser):
        """验证 always_ff 驱动信号名称正确性"""
        code = '''module t; logic clk, d; always_ff @(posedge clk) d <= 1; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        dc = DriverCollector(parser)
        dc.collect(result.tree, '/tmp/t.sv')
        
        # 验证驱动信号名称
        assert 'd' in dc.drivers, f"期望驱动信号 'd', 实际: {list(dc.drivers.keys())}"
    
    def test_basic_ff_clock_name(self, parser):
        """验证时钟信号名称正确性"""
        code = '''module t; logic clk, d; always_ff @(posedge clk) d <= 1; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        dc = DriverCollector(parser)
        dc.collect(result.tree, '/tmp/t.sv')
        
        # 验证时钟信号名称
        assert 'clk' in dc.all_clocks, f"期望时钟 'clk', 实际: {dc.all_clocks}"
    
    def test_async_reset_signal_name(self, parser):
        """验证异步复位信号名称正确性"""
        code = '''module t; logic clk, rst_n, d; always_ff @(posedge clk or negedge rst_n) d <= 1; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        dc = DriverCollector(parser)
        dc.collect(result.tree, '/tmp/t.sv')
        
        # 验证复位信号名称
        assert 'rst_n' in dc.all_resets, f"期望复位 'rst_n', 实际: {dc.all_resets}"
    
    def test_sync_reset_signal_name(self, parser):
        """验证同步复位信号名称正确性"""
        code = '''module t; logic clk, rst, d; always_ff @(posedge clk) if (rst) d <= 0; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        dc = DriverCollector(parser)
        dc.collect(result.tree, '/tmp/t.sv')
        
        # 验证复位信号名称
        assert 'rst' in dc.all_resets, f"期望复位 'rst', 实际: {dc.all_resets}"
    
    def test_multi_signal_names(self, parser):
        """验证多信号驱动名称正确性"""
        code = '''module t; logic clk, a, b, c;
        always_ff @(posedge clk) a <= 1;
        always_ff @(posedge clk) b <= 2;
        endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        dc = DriverCollector(parser)
        dc.collect(result.tree, '/tmp/t.sv')
        
        # 验证多个驱动信号名称
        assert 'a' in dc.drivers, f"期望驱动信号 'a', 实际: {list(dc.drivers.keys())}"
        assert 'b' in dc.drivers, f"期望驱动信号 'b', 实际: {list(dc.drivers.keys())}"
    
    def test_comb_driver_signal(self, parser):
        """验证组合逻辑驱动信号名称"""
        code = '''module t; logic a, b, c; always_comb c = a + b; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        dc = DriverCollector(parser)
        dc.collect(result.tree, '/tmp/t.sv')
        
        # 验证组合逻辑驱动信号
        assert 'c' in dc.drivers, f"期望驱动信号 'c', 实际: {list(dc.drivers.keys())}"
    
    def test_assign_driver_signal(self, parser):
        """验证连续赋值驱动信号名称"""
        code = '''module t; logic a, b, c; assign c = a + b; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        dc = DriverCollector(parser)
        dc.collect(result.tree, '/tmp/t.sv')
        
        # 验证连续赋值驱动信号
        assert 'c' in dc.drivers, f"期望驱动信号 'c', 实际: {list(dc.drivers.keys())}"
    
    def test_semantic_consistency(self, parser):
        """验证语义层与追踪层一致性"""
        code = '''module t; logic clk, rst_n, d; always_ff @(posedge clk or negedge rst_n) d <= 1; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        
        # 语义层提取
        collector = SemanticCollector()
        collector.collect(result.tree, '/tmp/t.sv')
        nb_assigns = collector.get_by_type(NonBlockingAssign)
        
        # 追踪层提取
        dc = DriverCollector(parser)
        dc.collect(result.tree, '/tmp/t.sv')
        
        # 验证一致性
        for nb in nb_assigns:
            assert nb.lhs in dc.drivers, f"语义层驱动 '{nb.lhs}' 不在追踪层: {list(dc.drivers.keys())}"
    
    def test_clock_extraction_consistency(self, parser):
        """验证时钟提取一致性"""
        code = '''module t; logic clk, d; always_ff @(posedge clk) d <= 1; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        
        # 语义层提取
        collector = SemanticCollector()
        collector.collect(result.tree, '/tmp/t.sv')
        nb_assigns = collector.get_by_type(NonBlockingAssign)
        
        # 追踪层提取
        dc = DriverCollector(parser)
        dc.collect(result.tree, '/tmp/t.sv')
        
        # 验证时钟一致性
        for nb in nb_assigns:
            if nb.clock:
                assert nb.clock in dc.all_clocks, f"语义层时钟 '{nb.clock}' 不在追踪层: {dc.all_clocks}"
    
    def test_reset_extraction_consistency(self, parser):
        """验证复位提取一致性"""
        code = '''module t; logic clk, rst_n, d; always_ff @(posedge clk or negedge rst_n) d <= 1; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        
        # 语义层提取
        collector = SemanticCollector()
        collector.collect(result.tree, '/tmp/t.sv')
        nb_assigns = collector.get_by_type(NonBlockingAssign)
        
        # 追踪层提取
        dc = DriverCollector(parser)
        dc.collect(result.tree, '/tmp/t.sv')
        
        # 验证复位一致性
        for nb in nb_assigns:
            if nb.reset:
                assert nb.reset in dc.all_resets, f"语义层复位 '{nb.reset}' 不在追踪层: {dc.all_resets}"
