"""Driver 边界语法测试

测试各种边界语法场景，确保 DriverTracer 的鲁棒性
"""

import pytest
import sys
sys.path.insert(0, 'src')

from sv_manager import SVManager
from trace.driver import DriverCollector


class TestDriverEdgeCases:
    """边界语法测试"""
    
    @pytest.fixture
    def parser(self):
        return SVManager()
    
    @pytest.fixture
    def test_file(self):
        return 'tests/sv_cases/driver/driver_edge_cases.sv'
    
    def test_01_generate_for(self, parser, test_file):
        """1. Generate For 中的驱动"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
        
        # 应该有时钟
        assert 'clk' in dc.all_clocks
    
    def test_02_multi_always_ff(self, parser, test_file):
        """2. 多个 always_ff 块"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有多个驱动信号
        assert len(dc.drivers) >= 2
    
    def test_03_nested_if(self, parser, test_file):
        """3. 嵌套 if 语句"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_04_case(self, parser, test_file):
        """4. Case 语句"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_05_continuous_assign(self, parser, test_file):
        """5. 连续赋值"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_06_always_comb(self, parser, test_file):
        """6. AlwaysComb"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
    
    def test_07_negedge_clk(self, parser, test_file):
        """7. 下降沿时钟"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有时钟
        assert len(dc.all_clocks) > 0
    
    def test_08_conditional(self, parser, test_file):
        """8. 条件赋值"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(dc.drivers) > 0
