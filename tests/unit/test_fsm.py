#!/usr/bin/env python3
"""
FSMExtractor 单元测试
"""
import sys
import os
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from parse.parser import SVParser
from debug.fsm import FSMExtractor


class TestFSMExtractor(unittest.TestCase):
    """FSMExtractor 测试类"""
    
    def test_simple_fsm(self):
        """测试简单状态机"""
        code = """
        module fsm(input clk, input rst_n);
            logic [1:0] state, next_state;
            
            always_ff @(posedge clk or negedge rst_n)
                if (!rst_n) state <= 2'b00;
                else state <= next_state;
            
            always_comb
                case (state)
                    2'b00: next_state = 2'b01;
                    2'b01: next_state = 2'b10;
                    2'b10: next_state = 2'b00;
                endcase
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
            f.flush()
            
            parser = SVParser()
            parser.parse_file(f.name)
            
            extractor = FSMExtractor(parser)
            fsm_list = extractor.extract()
            
            self.assertGreaterEqual(len(fsm_list), 1)
            fsm = fsm_list[0]
            self.assertEqual(fsm.state_var, 'state')
            self.assertGreaterEqual(len(fsm.states), 2)
        
        os.unlink(f.name)
    
    def test_fsm_with_enum(self):
        """测试 typedef enum 状态机"""
        code = """
        module fsm(input clk, input rst_n);
            typedef enum logic [1:0] {IDLE, RUN, DONE} state_t;
            state_t state, next_state;
            
            always_ff @(posedge clk or negedge rst_n)
                if (!rst_n) state <= IDLE;
                else state <= next_state;
            
            always_comb
                case (state)
                    IDLE: next_state = RUN;
                    RUN: next_state = DONE;
                    DONE: next_state = IDLE;
                endcase
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
            f.flush()
            
            parser = SVParser()
            parser.parse_file(f.name)
            
            extractor = FSMExtractor(parser)
            fsm_list = extractor.extract()
            
            self.assertGreaterEqual(len(fsm_list), 1)
            fsm = fsm_list[0]
            state_names = [s.name for s in fsm.states]
            self.assertIn('IDLE', state_names)
            self.assertIn('RUN', state_names)
        
        os.unlink(f.name)


if __name__ == '__main__':
    unittest.main()
