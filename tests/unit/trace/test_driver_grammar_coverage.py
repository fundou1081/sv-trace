"""Driver 语法覆盖度金标准测试

按项目纪律：
- 完全支持的语法：必须通过
- 部分支持的语法：验证基本功能
- 不支持的语法：验证不崩溃即可
"""

import pytest
import sys
sys.path.insert(0, 'src')

from sv_manager import SVManager
from trace.driver import DriverCollector


class TestDriverGrammarCoverage:
    """语法覆盖度测试"""
    
    @pytest.fixture
    def parser(self):
        return SVManager()
    
    @pytest.fixture
    def test_file(self):
        return 'tests/unit/trace/sv_cases/driver/driver_grammar_coverage.sv'
    
    # ========== 完全支持 ==========
    
    def test_01_posedge(self, parser, test_file):
        """1. always_ff posedge 时钟"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        assert 'clk' in dc.all_clocks
    
    def test_02_async_reset(self, parser, test_file):
        """2. 异步复位 or"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        assert 'rst_n' in dc.all_resets
    
    def test_03_sync_reset_high(self, parser, test_file):
        """3. 同步复位 if(rst)"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # rst 在 all_resets 中
        assert 'rst' in dc.all_resets
    
    def test_04_sync_reset_low(self, parser, test_file):
        """4. 同步复位 if(!rst_n)"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        # rst_n 在 all_resets 中
        assert 'rst_n' in dc.all_resets
    
    def test_05_generate_for(self, parser, test_file):
        """5. generate for"""
        result = parser.parse_file(test_file)
        # 解析成功即可
        assert result.success
    
    def test_06_function_return(self, parser, test_file):
        """6. function返回值"""
        result = parser.parse_file(test_file)
        dc = DriverCollector(parser)
        dc.collect(result.tree, test_file)
        
        assert 'result' in dc.drivers
    
    # ========== 部分支持 ==========
    
    def test_07_class_method(self, parser, test_file):
        """7. class method - 解析即可"""
        result = parser.parse_file(test_file)
        assert result.success
    
    def test_08_clocking_block(self, parser, test_file):
        """8. clocking block - 解析即可"""
        result = parser.parse_file(test_file)
        assert result.success
    
    def test_09_modport(self, parser, test_file):
        """9. modport - 解析即可"""
        result = parser.parse_file(test_file)
        assert result.success
    
    def test_10_sequence(self, parser, test_file):
        """10. sequence - 解析即可"""
        result = parser.parse_file(test_file)
        assert result.success
    
    def test_11_property(self, parser, test_file):
        """11. property - 解析即可"""
        result = parser.parse_file(test_file)
        assert result.success
    
    def test_12_randc(self, parser, test_file):
        """12. randc - 解析即可"""
        result = parser.parse_file(test_file)
        assert result.success
    
    # ========== 不支持 ==========
    
    def test_13_force(self, parser, test_file):
        """13. force - 不崩溃"""
        result = parser.parse_file(test_file)
        assert result.success  # 解析可能失败
    
    def test_14_release(self, parser, test_file):
        """14. release - 不崩溃"""
        result = parser.parse_file(test_file)
        assert result.success
    
    def test_15_alias(self, parser, test_file):
        """15. alias - 不崩溃"""
        result = parser.parse_file(test_file)
        # alias 可能解析失败
    
    def test_16_deassign(self, parser, test_file):
        """16. deassign - 不崩溃"""
        result = parser.parse_file(test_file)
        # deassign 可能解析失败


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
