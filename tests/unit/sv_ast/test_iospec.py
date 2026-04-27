import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

#!/usr/bin/env python3
"""
IOSpecExtractor 单元测试
"""
import sys
import os
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from parse.parser import SVParser
from debug.iospec import IOSpecExtractor


class TestIOSpecExtractor(unittest.TestCase):
    """IOSpecExtractor 测试类"""
    
    def test_simple_io(self):
        """测试简单 IO"""
        code = """
        module simple_io(
            input clk,
            input rst_n,
            input [7:0] data_in,
            output [7:0] data_out
        );
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
            f.flush()
            
            parser = SVParser()
            parser.parse_file(f.name)
            
            extractor = IOSpecExtractor(parser)
            spec = extractor.extract('simple_io')
            
            self.assertEqual(spec.module_name, 'simple_io')
            self.assertEqual(len(spec.ports), 4)
        
        os.unlink(f.name)
    
    def test_port_direction(self):
        """测试端口方向"""
        code = """
        module directions(
            input clk,
            output [7:0] data_out,
            inout [7:0] data_bus
        );
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
            f.flush()
            
            parser = SVParser()
            parser.parse_file(f.name)
            
            extractor = IOSpecExtractor(parser)
            spec = extractor.extract('directions')
            
            directions = {p.name: p.direction.value for p in spec.ports}
            self.assertEqual(directions.get('clk'), 'input')
            self.assertEqual(directions.get('data_out'), 'output')
            self.assertEqual(directions.get('data_bus'), 'inout')
        
        os.unlink(f.name)
    
    def test_port_category(self):
        """测试端口分类"""
        code = """
        module categories(
            input clk,
            input rst_n,
            input valid,
            input [7:0] data,
            output ready,
            output [7:0] result
        );
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
            f.flush()
            
            parser = SVParser()
            parser.parse_file(f.name)
            
            extractor = IOSpecExtractor(parser)
            spec = extractor.extract('categories')
            
            categories = {p.name: p.category.value for p in spec.ports}
            self.assertEqual(categories.get('clk'), 'clock')
            self.assertEqual(categories.get('rst_n'), 'reset')
            self.assertEqual(categories.get('valid'), 'control')
            self.assertEqual(categories.get('data'), 'data')
        
        os.unlink(f.name)
    
    def test_port_width(self):
        """测试端口宽度"""
        code = """
        module widths(
            input [31:0] data32,
            input [7:0] data8,
            input single
        );
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
            f.flush()
            
            parser = SVParser()
            parser.parse_file(f.name)
            
            extractor = IOSpecExtractor(parser)
            spec = extractor.extract('widths')
            
            widths = {p.name: p.width for p in spec.ports}
            self.assertEqual(widths.get('data32'), 32)
            self.assertEqual(widths.get('data8'), 8)
            self.assertEqual(widths.get('single'), 1)
        
        os.unlink(f.name)


if __name__ == '__main__':
    unittest.main()
