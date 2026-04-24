#!/usr/bin/env python3
"""
DriverTracer 单元测试
"""
import sys
import os
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from parse.parser import SVParser
from trace.driver import DriverTracer


class TestDriverTracer(unittest.TestCase):
    """DriverTracer 测试类"""
    
    def test_assign_driver(self):
        """测试 assign 驱动"""
        code = """
        module top;
            wire [7:0] a, b;
            assign a = 8'hFF;
            assign b = a + 1;
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
            f.flush()
            
            parser = SVParser()
            parser.parse_file(f.name)
            
            tracer = DriverTracer(parser)
            drivers = tracer.find_driver('a')
            
            self.assertGreaterEqual(len(drivers), 1)
        
        os.unlink(f.name)
    
    def test_ff_driver(self):
        """测试 always_ff 驱动"""
        code = """
        module top;
            logic clk;
            logic [7:0] data, out;
            always_ff @(posedge clk) begin
                out <= data;
            end
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
            f.flush()
            
            parser = SVParser()
            parser.parse_file(f.name)
            
            tracer = DriverTracer(parser)
            drivers = tracer.find_driver('out')
            
            self.assertGreaterEqual(len(drivers), 1)
        
        os.unlink(f.name)
    
    def test_comb_driver(self):
        """测试 always_comb 驱动"""
        code = """
        module top;
            logic [7:0] a, b, c;
            always_comb begin
                c = a + b;
            end
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
            f.flush()
            
            parser = SVParser()
            parser.parse_file(f.name)
            
            tracer = DriverTracer(parser)
            drivers = tracer.find_driver('c')
            
            self.assertGreaterEqual(len(drivers), 1)
        
        os.unlink(f.name)
    
    def test_no_driver(self):
        """测试无驱动信号"""
        code = """
        module top;
            logic [7:0] undriven;
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
            f.flush()
            
            parser = SVParser()
            parser.parse_file(f.name)
            
            tracer = DriverTracer(parser)
            drivers = tracer.find_driver('undriven')
            
            self.assertEqual(len(drivers), 0)
        
        os.unlink(f.name)


if __name__ == '__main__':
    unittest.main()
