"""LoadTracer 语义验证测试

深入验证负载提取结果与语义一致性
符合铁律 4: 模型即契约
"""

import pytest
import sys
sys.path.insert(0, 'src')

from sv_manager import SVManager
from trace.load import LoadTracer


class TestLoadSemanticValidation:
    """语义验证测试"""
    
    @pytest.fixture
    def parser(self):
        return SVManager()
    
    def test_basic_load_signal_name(self, parser):
        """验证赋值右值信号名称正确性"""
        code = '''module t; logic a, b, c; assign c = a + b; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # 验证负载信号名称
        assert 'a' in tracer.all_signals, f"期望负载 'a', 实际: {tracer.all_signals}"
        assert 'b' in tracer.all_signals, f"期望负载 'b', 实际: {tracer.all_signals}"
    
    def test_array_index_load(self, parser):
        """验证数组索引负载"""
        code = '''module t; logic [7:0] arr [0:3]; logic [1:0] idx; assign arr[idx] = 8'h0; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # 验证数组索引负载
        assert 'arr' in tracer.all_signals, f"期望负载 'arr', 实际: {tracer.all_signals}"
        assert 'idx' in tracer.all_signals, f"期望负载 'idx', 实际: {tracer.all_signals}"
    
    def test_if_condition_load(self, parser):
        """验证 if 条件负载"""
        code = '''module t; logic clk, rst_n, en; logic [7:0] data; always_ff @(posedge clk) if (en) data <= 8'h0; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # 验证条件负载
        assert 'en' in tracer.all_signals, f"期望负载 'en', 实际: {tracer.all_signals}"
    
    def test_case_condition_load(self, parser):
        """验证 case 条件负载"""
        code = '''module t; logic [1:0] sel; logic [7:0] data; always_comb case (sel) 2'b00: data = 8'h0; endcase endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # 验证 case 负载
        assert 'sel' in tracer.all_signals, f"期望负载 'sel', 实际: {tracer.all_signals}"
    
    def test_function_call_load(self, parser):
        """验证函数调用负载"""
        code = '''module t; logic [7:0] a, b, c; function logic [7:0] add(input logic [7:0] x, y); return x + y; endfunction assign c = add(a, b); endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # 验证函数参数负载
        assert 'a' in tracer.all_signals, f"期望负载 'a', 实际: {tracer.all_signals}"
        assert 'b' in tracer.all_signals, f"期望负载 'b', 实际: {tracer.all_signals}"
    
    def test_nested_expression_load(self, parser):
        """验证嵌套表达式负载"""
        code = '''module t; logic [7:0] a, b, c, d; assign d = (a + b) * c; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # 验证嵌套表达式负载
        assert 'a' in tracer.all_signals, f"期望负载 'a', 实际: {tracer.all_signals}"
        assert 'b' in tracer.all_signals, f"期望负载 'b', 实际: {tracer.all_signals}"
        assert 'c' in tracer.all_signals, f"期望负载 'c', 实际: {tracer.all_signals}"
    
    def test_complex_expression_load(self, parser):
        """验证复杂表达式负载"""
        code = '''module t; logic [7:0] a, b, c, d; assign d = a ? b + c : c + 1; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # 验证三元表达式负载
        assert 'a' in tracer.all_signals, f"期望负载 'a', 实际: {tracer.all_signals}"
        assert 'b' in tracer.all_signals, f"期望负载 'b', 实际: {tracer.all_signals}"
        assert 'c' in tracer.all_signals, f"期望负载 'c', 实际: {tracer.all_signals}"
    
    def test_nonblocking_load(self, parser):
        """验证非阻塞赋值的负载"""
        code = '''module t; logic clk, a, b; always_ff @(posedge clk) b <= a; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # 验证非阻塞赋值右值负载
        assert 'a' in tracer.all_signals, f"期望负载 'a', 实际: {tracer.all_signals}"
    
    def test_multi_load(self, parser):
        """验证多负载"""
        code = '''module t; logic a, b, c, d; assign d = a + b + c; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # 验证多个负载
        assert len(tracer.all_signals) >= 3, f"期望至少 3 个负载, 实际: {len(tracer.all_signals)}"
    
    def test_find_load(self, parser):
        """验证查找特定负载"""
        code = '''module t; logic a, b, c; assign c = a + b; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # 查找特定信号的负载
        loads = tracer.find_load('a')
        assert len(loads) > 0, f"期望 'a' 有负载, 实际: {loads}"
