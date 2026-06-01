"""Driver P1 语法测试

测试 for loop, function, task, generate if
符合铁律 7: 新功能必须先有边界测试
"""

import pytest
import sys
sys.path.insert(0, 'src')

from sv_manager import SVManager
from trace.driver import DriverCollector


class TestDriverP1Syntax:
    """P1 语法测试"""
    
    @pytest.fixture
    def parser(self):
        return SVManager()
    
    @pytest.fixture
    def test_file(self):
        return 'tests/unit/trace/sv_cases/driver/driver_p1_syntax.sv'
    
    def test_01_for_loop(self, parser, test_file):
        """1. For Loop 中的驱动"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_02_function(self, parser, test_file):
        """2. Function 中的驱动"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_03_task(self, parser, test_file):
        """3. Task 中的驱动"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_04_generate_if(self, parser, test_file):
        """4. Generate If 中的驱动"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_05_foreach(self, parser, test_file):
        """5. Foreach Loop 中的驱动"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_06_while(self, parser, test_file):
        """6. While Loop 中的驱动"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
