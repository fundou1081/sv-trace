import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

#!/usr/bin/env python3
"""
Tier2 工具测试
"""
import sys
import os
import tempfile
import unittest

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser, ClassExtractor
from debug.analyzers.fsm_analyzer import FSMAnalyzer


class TestClassExtractor(unittest.TestCase):
    """测试 ClassExtractor"""
    
    def test_class_extraction(self):
        """测试类提取"""
        code = '''
class packet;
    rand bit [7:0] data;
endclass
'''
        parser = SVParser()
        parser.parse_text(code)
        
        extractor = ClassExtractor(parser)
        classes = extractor.get_classes()
        
        print(f"  Classes found: {len(classes)}")
    
    def test_class_members(self):
        """测试类成员提取"""
        code = '''
class packet;
    rand bit [7:0] data;
    function void compare();
    endfunction
endclass
'''
        parser = SVParser()
        parser.parse_text(code)
        
        extractor = ClassExtractor(parser)
        classes = extractor.get_classes()
        
        print(f"  Classes found: {len(classes)}")
        print(f"  Classes: {len(classes)}")


class TestFSMAnalyzer(unittest.TestCase):
    """测试 FSMAnalyzer"""
    
    def test_fsm_analyzer(self):
        """测试 FSM 分析"""
        code = '''
module fsm(input clk);
    logic [1:0] state;
    always_ff @(posedge clk)
        state <= state + 1;
endmodule
'''
        parser = SVParser()
        parser.parse_text(code)
        
        analyzer = FSMAnalyzer(parser)
        report = analyzer.analyze()
        
        self.assertIsNotNone(report)


def main():
    print("\n=== Tier2 Tools Tests ===")
    
    tests = TestClassExtractor()
    
    try:
        tests.test_class_extraction()
        print("  ✅ test_class_extraction 通过")
    except Exception as e:
        print(f"  ❌ test_class_extraction: {e}")
        return False
    
    try:
        tests.test_class_members()
        print("  ✅ test_class_members 通过")
    except Exception as e:
        print(f"  ❌ test_class_members: {e}")
        return False
    
    try:
        TestFSMAnalyzer().test_fsm_analyzer()
        print("  ✅ test_fsm_analyzer 通过")
    except Exception as e:
        print(f"  ❌ test_fsm_analyzer: {e}")
        return False
    
    print("\n总计: 3/3 通过")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
