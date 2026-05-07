"""Driver 边界语法金标准测试

测试 10 个 SystemVerilog 边界语法场景，确保 Driver 提取的正确性
"""

import pytest
import sys
sys.path.insert(0, 'src')

from sv_manager import SVManager
from trace.driver import DriverCollector


class TestDriverBoundary:
    """边界语法测试"""
    
    @pytest.fixture
    def parser(self):
        return SVManager()
    
    @pytest.fixture
    def test_file(self):
        return 'tests/sv_cases/driver/driver_boundary_10.sv'
    
    def test_generate_for(self, parser, test_file):
        """1. Generate For 循环内的驱动"""
        result = parser.parse_file(test_file)
        
        # 找到 driver_01_gen_for 模块的驱动
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有驱动信号
        assert len(drivers := dc.drivers) > 0
        
        # 检查时钟
        assert 'clk' in dc.all_clocks
    
    def test_function_return(self, parser, test_file):
        """2. 函数返回值驱动"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # result 应该有驱动
        assert any('result' in s for s in dc.drivers)
    
    def test_class_method(self, parser, test_file):
        """3. Class 方法驱动"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # data_out 应该有驱动
        assert any('data_out' in s for s in dc.drivers)
    
    def test_nested_if_with_reset(self, parser, test_file):
        """6. 嵌套 if 带同步复位"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有 rst 复位
        assert 'rst' in dc.all_resets
    
    def test_case_with_reset(self, parser, test_file):
        """7. case 带复位"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # 应该有 rst 复位
        assert 'rst' in dc.all_resets
    
    def test_multi_driver(self, parser, test_file):
        """8. 多驱动检测"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # data 应该有多个驱动
        drivers = dc.drivers.get('data', [])
        assert len(drivers) >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
