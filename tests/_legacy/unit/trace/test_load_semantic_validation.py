"""LoadTracer 语义验证测试

修正后的测试 — 反映 LoadTracer 的正确语义：
- Load 表示 "LHS 被 RHS 驱动/加载"
- all_signals 包含的是"被赋值的信号"（LHS）
- find_load(signal) 返回驱动该信号的源（RHS）

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
        """验证赋值负载语义: assign c = a + b
        
        语义: c 被 a 和 b 加载 (c ← a, c ← b)
        all_signals 包含 'c'（被赋值的信号），不包含 'a' 'b'（驱动源）
        """
        code = '''module t; logic a, b, c; assign c = a + b; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # c 是被赋值的信号，在 all_signals 中
        # a 和 b 是驱动源，不在 all_signals 中
        assert 'c' in tracer.all_signals, f"期望 'c' (被赋值), 实际: {tracer.all_signals}"
        assert 'a' not in tracer.all_signals, f"期望 'a' (驱动源) 不在 all_signals, 实际: {tracer.all_signals}"
        assert 'b' not in tracer.all_signals, f"期望 'b' (驱动源) 不在 all_signals, 实际: {tracer.all_signals}"
        
        # 验证 c 的负载
        loads = tracer.find_load('c')
        assert len(loads) == 2, f"期望 c 有 2 个负载, 实际: {len(loads)}"
        load_sigs = [lp.load_by for lp in loads]
        assert 'a' in load_sigs, f"期望 'a' 在负载中, 实际: {load_sigs}"
        assert 'b' in load_sigs, f"期望 'b' 在负载中, 实际: {load_sigs}"
    
    def test_array_index_load(self, parser):
        """验证数组索引负载: assign arr[idx] = 8'h0
        
        语义: arr 被加载 (写入地址 arr[idx])
        arr 在 all_signals 中
        """
        code = '''module t; logic [7:0] arr [0:3]; logic [1:0] idx; assign arr[idx] = 8'h0; endmodule'''
        with open('/tmp/test_array_idx.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/test_array_idx.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/test_array_idx.sv')
        
        # arr 被写入，在 all_signals 中
        assert 'arr' in tracer.all_signals, f"期望负载 'arr', 实际: {tracer.all_signals}"
    
    def test_if_condition_load(self, parser):
        """验证 if 条件中的信号被提取: if (en) data <= 1
        
        语义: 
        - en 在条件中被读取 (条件负载)
        - data 在非阻塞赋值中被加载
        两者都在 all_signals 中
        """
        code = '''module t; logic clk, en, data; always_ff @(posedge clk) if (en) data <= 1; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # data 被赋值，在 all_signals 中
        # en 在 if 条件中被读取，作为条件负载也在 all_signals 中
        assert 'en' in tracer.all_signals, f"期望 'en' (条件负载), 实际: {tracer.all_signals}"
        assert 'data' in tracer.all_signals, f"期望 'data' (被赋值), 实际: {tracer.all_signals}"
    
    def test_case_condition_load(self, parser):
        """验证 case 条件中的负载: case (sel)
        
        语义: sel 在 case 条件中被读取
        out 被赋值字面量
        sel 和 out 都在 all_signals 中
        """
        code = '''module t; logic [1:0] sel; logic [7:0] out; always_comb case (sel) 2'b00: out = 8'hAA; endcase endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # sel 在 case 条件中被读取，作为条件负载
        # out 被赋值
        assert 'sel' in tracer.all_signals, f"期望 'sel' (条件负载), 实际: {tracer.all_signals}"
        assert 'out' in tracer.all_signals, f"期望 'out' (被赋值), 实际: {tracer.all_signals}"
    
    def test_function_call_load(self, parser):
        """验证函数调用中的负载: c = add(a, b)
        
        语义: c 被加载 (函数返回值写入 c)
        函数参数 a, b 是驱动源，不在 all_signals 中
        """
        code = '''module t; logic [7:0] a, b, c; function logic [7:0] add(input logic [7:0] x, y); return x + y; endfunction assign c = add(a, b); endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # c 是被赋值的信号，在 all_signals 中
        # add 是函数名，不算负载信号
        assert 'c' in tracer.all_signals, f"期望负载 'c', 实际: {tracer.all_signals}"
    
    def test_nested_expression_load(self, parser):
        """验证嵌套表达式负载: assign d = (a + b) * c
        
        语义: d 被 a, b, c 加载
        d 在 all_signals 中，a, b, c 不在
        """
        code = '''module t; logic [7:0] a, b, c, d; assign d = (a + b) * c; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # d 是被赋值的信号，在 all_signals 中
        # a, b, c 是驱动源，不在 all_signals 中
        assert 'd' in tracer.all_signals, f"期望 'd' (被赋值), 实际: {tracer.all_signals}"
        assert 'a' not in tracer.all_signals, f"期望 'a' (驱动源) 不在 all_signals, 实际: {tracer.all_signals}"
        assert 'b' not in tracer.all_signals, f"期望 'b' (驱动源) 不在 all_signals, 实际: {tracer.all_signals}"
        assert 'c' not in tracer.all_signals, f"期望 'c' (驱动源) 不在 all_signals, 实际: {tracer.all_signals}"
    
    def test_complex_expression_load(self, parser):
        """验证三元表达式负载: assign d = a ? b + c : c + 1
        
        语义: d 被 a, b, c 加载 (a 是条件，b/c 是分支值)
        d 在 all_signals 中
        """
        code = '''module t; logic [7:0] a, b, c, d; assign d = a ? b + c : c + 1; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # d 是被赋值的信号，在 all_signals 中
        assert 'd' in tracer.all_signals, f"期望 'd' (被赋值), 实际: {tracer.all_signals}"
    
    def test_nonblocking_load(self, parser):
        """验证非阻塞赋值的负载: b <= a
        
        语义: b 被 a 加载 (b 的下一个值取决于 a)
        b 在 all_signals 中，a 不在
        """
        code = '''module t; logic clk, a, b; always_ff @(posedge clk) b <= a; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # b 是被赋值的信号，在 all_signals 中
        # a 是驱动源，不在 all_signals 中
        assert 'b' in tracer.all_signals, f"期望 'b' (被赋值), 实际: {tracer.all_signals}"
        assert 'a' not in tracer.all_signals, f"期望 'a' (驱动源) 不在 all_signals, 实际: {tracer.all_signals}"
        
        # 验证 b 的负载是 a
        loads = tracer.find_load('b')
        assert len(loads) >= 1, f"期望 b 有负载, 实际: {loads}"
    
    def test_multi_load(self, parser):
        """验证多负载: assign d = a + b + c
        
        语义: d 被 a, b, c 加载
        d 在 all_signals 中，a, b, c 不在
        """
        code = '''module t; logic a, b, c, d; assign d = a + b + c; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # d 是被赋值的信号，在 all_signals 中
        # a, b, c 是驱动源，不在 all_signals 中
        assert 'd' in tracer.all_signals, f"期望 'd' (被赋值), 实际: {tracer.all_signals}"
        assert 'a' not in tracer.all_signals, f"期望 'a' (驱动源) 不在 all_signals, 实际: {tracer.all_signals}"
        assert 'b' not in tracer.all_signals, f"期望 'b' (驱动源) 不在 all_signals, 实际: {tracer.all_signals}"
        assert 'c' not in tracer.all_signals, f"期望 'c' (驱动源) 不在 all_signals, 实际: {tracer.all_signals}"
    
    def test_find_load(self, parser):
        """验证 find_load API: assign c = a + b
        
        语义:
        - c 是被赋值的信号
        - find_load('c') 返回 c 的负载 (a 和 b)
        - find_load('a') 返回空 (a 没有被加载)
        """
        code = '''module t; logic a, b, c; assign c = a + b; endmodule'''
        with open('/tmp/t.sv', 'w') as f:
            f.write(code)
        
        result = parser.parse_file('/tmp/t.sv')
        tracer = LoadTracer()
        tracer.collect(result.tree, '/tmp/t.sv')
        
        # find_load('c') 查找被 c 加载的信号
        # c ← a, c ← b，所以 c 有两个负载
        loads = tracer.find_load('c')
        assert len(loads) == 2, f"期望 c 有 2 个负载, 实际: {loads}"
        load_sigs = [lp.load_by for lp in loads]
        assert 'a' in load_sigs, f"期望 'a' 在负载中, 实际: {load_sigs}"
        assert 'b' in load_sigs, f"期望 'b' 在负载中, 实际: {load_sigs}"
        
        # find_load('a') 查找被 a 加载的信号
        # a 是驱动源，没有信号被 a 加载
        loads_a = tracer.find_load('a')
        assert len(loads_a) == 0, f"期望 'a' 没有负载, 实际: {loads_a}"