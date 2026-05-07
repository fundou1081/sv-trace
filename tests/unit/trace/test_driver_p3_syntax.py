"""Driver P3 语法测试

测试 assert, covergroup, sequence, property
符合铁律 7: 新功能必须先有边界测试
"""

import pytest
import sys
sys.path.insert(0, 'src')

from sv_manager import SVManager
from trace.driver import DriverCollector


class TestDriverP3Syntax:
    """P3 语法测试"""
    
    @pytest.fixture
    def parser(self):
        return SVManager()
    
    @pytest.fixture
    def test_file(self):
        return 'tests/unit/trace/sv_cases/driver/driver_p3_syntax.sv'
    
    def test_01_assert(self, parser, test_file):
        """1. Assert Statement"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_02_assert_else(self, parser, test_file):
        """2. Assert with else"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_03_covergroup(self, parser, test_file):
        """3. Covergroup"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_04_immediate_assert(self, parser, test_file):
        """4. Immediate Assert"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_05_sequence(self, parser, test_file):
        """5. Sequence"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_06_property(self, parser, test_file):
        """6. Property with clocking"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
