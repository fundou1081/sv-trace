"""LoadTracer 测试

测试负载追踪功能
符合铁律 14: 测试分层强制化
"""

import pytest
import sys
sys.path.insert(0, 'src')

from sv_manager import SVManager
from trace.load import LoadTracer


class TestLoadTracer:
    """LoadTracer 测试"""
    
    @pytest.fixture
    def parser(self):
        return SVManager()
    
    def test_basic_load(self, parser):
        """基本负载测试"""
        code = '''module t; logic a, b, c; assign c = a + b; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # 应该有负载信号
        assert len(tracer.all_signals) > 0
    
    def test_always_ff_load(self, parser):
        """always_ff 负载测试"""
        code = '''module t; logic clk, a, b; always_ff @(posedge clk) a <= b; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # 应该有负载信号
        assert len(tracer.all_signals) > 0
    
    def test_conditional_load(self, parser):
        """条件负载测试"""
        code = '''module t; logic clk, rst, a, b; always_ff @(posedge clk) if (rst) a <= b; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # 应该有负载信号
        assert len(tracer.all_signals) > 0
    
    def test_find_load(self, parser):
        """查找负载测试"""
        code = '''module t; logic a, b, c; assign c = a + b; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # 查找特定信号
        loads = tracer.find_load('a')
        assert isinstance(loads, list)
