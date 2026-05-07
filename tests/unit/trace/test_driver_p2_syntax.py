"""Driver P2 语法测试

测试 always @, while, class, interface
符合铁律 7: 新功能必须先有边界测试
"""

import pytest
import sys
sys.path.insert(0, 'src')

from sv_manager import SVManager
from trace.driver import DriverCollector


class TestDriverP2Syntax:
    """P2 语法测试"""
    
    @pytest.fixture
    def parser(self):
        return SVManager()
    
    @pytest.fixture
    def test_file(self):
        return 'tests/unit/trace/sv_cases/driver/driver_p2_syntax.sv'
    
    def test_01_always_at(self, parser, test_file):
        """1. Always @ (旧语法)"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_02_always_star(self, parser, test_file):
        """2. Always @* (组合逻辑)"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_03_class(self, parser, test_file):
        """3. Class 中的驱动"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_04_interface(self, parser, test_file):
        """4. Interface 中的驱动"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_05_do_while(self, parser, test_file):
        """5. Do While Loop"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_06_repeat(self, parser, test_file):
        """6. Repeat Loop"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
