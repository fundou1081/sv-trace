"""
Dependency 工具测试 (TDD)
目标: src/trace/dependency.py
"""

import pytest
import sys
sys.path.insert(0, '../../src')
from parse import SVParser
from trace.dependency import DependencyAnalyzer

RTL_DEP = '''module dut(input a, b, output y);
    logic t;
    assign t = a & b;
    assign y = t;
endmodule'''

RTL_MULTI = '''module dut(input a, b, c, output y);
    logic t1, t2;
    assign t1 = a + b;
    assign t2 = t1 * c;
    assign y = t2;
endmodule'''

class TestDependencyBasic:
    @pytest.mark.unit
    def test_simple(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_DEP)
        da = DependencyAnalyzer(parser)
        assert da is not None
    
    @pytest.mark.unit
    def test_multi(self):
        parser = SVParser(verbose=False)
        tree = parser.parse_text(RTL_MULTI)
        da = DependencyAnalyzer(parser)
        assert da is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
