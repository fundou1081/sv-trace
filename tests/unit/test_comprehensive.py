#!/usr/bin/env python3
"""
综合测试 - 覆盖已知问题域
"""
import sys
import os
import unittest
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from parse.parser import SVParser
from trace.driver import DriverTracer
from debug.fsm import FSMExtractor
from debug.iospec import IOSpecExtractor
from debug.dependency import ModuleDependencyAnalyzer


class TestIOSpecParameterized(unittest.TestCase):
    """IOSpec - 参数化相关测试"""
    
    def test_param_width_WIDTH_1_0(self):
        """参数化格式: WIDTH-1:0"""
        code = """
        module m #(
            parameter WIDTH = 8
        )(input [WIDTH-1:0] d);
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        extractor = IOSpecExtractor(parser)
        spec = extractor.extract('m')
        widths = {p.name: p.width for p in spec.ports}
        self.assertEqual(widths.get('d'), 1)  # 参数化，设为1
        os.unlink(f.name)
    
    def test_param_width_DW_1_0(self):
        """参数化格式: DW-1:0"""
        code = """
        module m #(
            parameter DW = 16
        )(input [DW-1:0] data);
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        extractor = IOSpecExtractor(parser)
        spec = extractor.extract('m')
        widths = {p.name: p.width for p in spec.ports}
        self.assertEqual(widths.get('data'), 1)  # 参数化
        os.unlink(f.name)
    
    def test_numeric_width(self):
        """数字格式: [31:0]"""
        code = """
        module m(input [31:0] data);
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        extractor = IOSpecExtractor(parser)
        spec = extractor.extract('m')
        widths = {p.name: p.width for p in spec.ports}
        self.assertEqual(widths.get('data'), 32)  # 正确解析
        os.unlink(f.name)
    
    def test_single_bit(self):
        """单bit: 无宽度"""
        code = """
        module m(input clk, input enable);
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        extractor = IOSpecExtractor(parser)
        spec = extractor.extract('m')
        widths = {p.name: p.width for p in spec.ports}
        self.assertEqual(widths.get('clk'), 1)
        self.assertEqual(widths.get('enable'), 1)
        os.unlink(f.name)


class TestDependencyInstanceParams(unittest.TestCase):
    """ModuleDependency - 实例参数测试"""
    
    def test_single_param(self):
        """单个参数"""
        code = """
        module ram #(parameter AW=8)();
        endmodule
        module top;
            ram #(.AW(10)) u_ram();
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        analyzer = ModuleDependencyAnalyzer(parser)
        graph = analyzer.analyze()
        top = graph.modules['top']
        inst = top.instances[0]
        self.assertEqual(inst.parameters.get('AW'), '10')
        os.unlink(f.name)
    
    def test_multiple_params(self):
        """多个参数"""
        code = """
        module ram #(parameter AW=8, parameter DW=32)();
        endmodule
        module top;
            ram #(.AW(12), .DW(64)) u_ram();
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        analyzer = ModuleDependencyAnalyzer(parser)
        graph = analyzer.analyze()
        top = graph.modules['top']
        inst = top.instances[0]
        self.assertEqual(inst.parameters.get('AW'), '12')
        self.assertEqual(inst.parameters.get('DW'), '64')
        os.unlink(f.name)
    
    def test_string_param(self):
        """字符串参数"""
        code = """
        module fifo #(parameter NAME="fifo")();
        endmodule
        module top;
            fifo #(.NAME("my_fifo")) u_fifo();
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        analyzer = ModuleDependencyAnalyzer(parser)
        graph = analyzer.analyze()
        top = graph.modules['top']
        inst = top.instances[0]
        self.assertEqual(inst.parameters.get('NAME'), '"my_fifo"')
        os.unlink(f.name)
    
    def test_hierarchy_with_params(self):
        """带参数的层次结构"""
        code = """
        module leaf #(parameter W=8)();
        endmodule
        module middle #(
            parameter A=4,
            parameter B=16
        )();
            leaf #(.W(B)) u_leaf();
        endmodule
        module top;
            middle #(.A(8), .B(32)) u_mid();
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        analyzer = ModuleDependencyAnalyzer(parser)
        graph = analyzer.analyze()
        
        top = graph.modules['top']
        self.assertEqual(top.instances[0].parameters.get('A'), '8')
        self.assertEqual(top.instances[0].parameters.get('B'), '32')
        
        middle = graph.modules['middle']
        self.assertEqual(middle.instances[0].parameters.get('W'), 'B')
        os.unlink(f.name)


class TestDriverPatterns(unittest.TestCase):
    """DriverTracer - 驱动模式测试"""
    
    def test_ff_posedge(self):
        """always_ff posedge"""
        code = """
        module m(input clk, output reg [7:0] d);
            always_ff @(posedge clk) d <= 8'h00;
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        tracer = DriverTracer(parser)
        drivers = tracer.find_driver('d')
        self.assertGreaterEqual(len(drivers), 1)
        os.unlink(f.name)
    
    def test_ff_negedge(self):
        """always_ff negedge"""
        code = """
        module m(input clk, output reg [7:0] d);
            always_ff @(negedge clk) d <= 8'h00;
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        tracer = DriverTracer(parser)
        drivers = tracer.find_driver('d')
        self.assertGreaterEqual(len(drivers), 1)
        os.unlink(f.name)
    
    def test_ff_async_reset(self):
        """always_ff 异步复位"""
        code = """
        module m(input clk, input rst_n, output reg [7:0] d);
            always_ff @(posedge clk or negedge rst_n)
                if (!rst_n) d <= 8'h00;
                else d <= d + 1;
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        tracer = DriverTracer(parser)
        drivers = tracer.find_driver('d')
        self.assertGreaterEqual(len(drivers), 1)
        os.unlink(f.name)
    
    def test_comb(self):
        """always_comb"""
        code = """
        module m(input [7:0] a, b, output [7:0] c);
            always_comb c = a + b;
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        tracer = DriverTracer(parser)
        drivers = tracer.find_driver('c')
        self.assertGreaterEqual(len(drivers), 1)
        os.unlink(f.name)
    
    def test_assign(self):
        """assign"""
        code = """
        module m(output [7:0] a);
            assign a = 8'hFF;
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        tracer = DriverTracer(parser)
        drivers = tracer.find_driver('a')
        self.assertGreaterEqual(len(drivers), 1)
        os.unlink(f.name)
    
    def test_case_driver(self):
        """case 语句驱动"""
        code = """
        module m(input clk, input [1:0] sel, output reg [7:0] out);
            always_ff @(posedge clk)
                case (sel)
                    2'b00: out <= 8'h00;
                    2'b01: out <= 8'hFF;
                    default: out <= 8'hAA;
                endcase
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        tracer = DriverTracer(parser)
        drivers = tracer.find_driver('out')
        self.assertGreaterEqual(len(drivers), 1)
        os.unlink(f.name)


class TestFSMPatterns(unittest.TestCase):
    """FSMExtractor - 状态机模式测试"""
    
    def test_binary_encoding(self):
        """二进制编码"""
        code = """
        module m(input clk, input rst_n);
            logic [1:0] state, next_state;
            always_ff @(posedge clk or negedge rst_n)
                if (!rst_n) state <= 2'b00;
                else state <= next_state;
            always_comb case (state)
                2'b00: next_state = 2'b01;
                2'b01: next_state = 2'b00;
            endcase
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        extractor = FSMExtractor(parser)
        fsm_list = extractor.extract()
        self.assertGreaterEqual(len(fsm_list), 1)
        os.unlink(f.name)
    
    def test_onehot_encoding(self):
        """One-Hot 编码"""
        code = """
        module m(input clk, input rst_n);
            logic [3:0] state, next_state;
            parameter IDLE=4'b0001, RUN=4'b0010, DONE=4'b0100;
            always_ff @(posedge clk or negedge rst_n)
                if (!rst_n) state <= IDLE;
                else state <= next_state;
            always_comb case (state)
                IDLE: next_state = RUN;
                RUN: next_state = DONE;
                DONE: next_state = IDLE;
            endcase
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        extractor = FSMExtractor(parser)
        fsm_list = extractor.extract()
        self.assertGreaterEqual(len(fsm_list), 1)
        os.unlink(f.name)


class TestDependencyHierarchy(unittest.TestCase):
    """ModuleDependency - 层次结构测试"""
    
    def test_three_level(self):
        """三层层次"""
        code = """
        module leaf();
        endmodule
        module middle();
            leaf u_leaf();
        endmodule
        module top();
            middle u_mid();
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        analyzer = ModuleDependencyAnalyzer(parser)
        graph = analyzer.analyze()
        
        self.assertIn('top', graph.root_modules)
        self.assertIn('leaf', graph.leaf_modules)
        self.assertIn('middle', graph.modules['top'].depends_on)
        self.assertIn('leaf', graph.modules['middle'].depends_on)
        os.unlink(f.name)
    
    def test_diamond(self):
        """菱形依赖"""
        code = """
        module leaf();
        endmodule
        module a();
            leaf u_leaf();
        endmodule
        module b();
            leaf u_leaf();
        endmodule
        module top();
            a u_a();
            b u_b();
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        analyzer = ModuleDependencyAnalyzer(parser)
        graph = analyzer.analyze()
        
        self.assertIn('leaf', graph.modules['a'].depends_on)
        self.assertIn('leaf', graph.modules['b'].depends_on)
        os.unlink(f.name)
    
    def test_multi_instance_same_module(self):
        """同模块多实例"""
        code = """
        module cell();
        endmodule
        module top();
            cell u0();
            cell u1();
            cell u2();
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
        parser = SVParser()
        parser.parse_file(f.name)
        analyzer = ModuleDependencyAnalyzer(parser)
        graph = analyzer.analyze()
        
        top = graph.modules['top']
        self.assertEqual(len(top.instances), 3)
        names = [i.instance_name for i in top.instances]
        self.assertIn('u0', names)
        self.assertIn('u1', names)
        self.assertIn('u2', names)
        os.unlink(f.name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
