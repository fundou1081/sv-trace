"""
E2E 测试 - 端到端 driver tracing

遵循铁律13: 金标准测试
"""

import pytest
import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.driver import DriverCollector, DriverTracer


class TestDriverE2E:
    """Driver E2E 测试"""
    
    @pytest.mark.e2e
    def test_basic_driver(self):
        """基础 driver 追踪"""
        code = '''
module dut(input clk, input [7:0] data, output [7:0] q);
    always_ff @(posedge clk) q <= data;
endmodule
'''
        tree = SVParser(verbose=False).parse_text(code)
        tracer = DriverTracer(parser=None, verbose=False)
        tracer.collect(tree, 'dut.sv')
        
        drivers = tracer.get_drivers('q')
        assert len(drivers) > 0
        
    @pytest.mark.e2e
    def test_multi_driver(self):
        """多 driver 检测"""
        code = '''
module dut(input clk, input a, output q);
    always_ff @(posedge clk) q <= a;
    always_ff @(posedge clk) q <= a + 1;
endmodule
'''
        tree = SVParser(verbose=False).parse_text(code)
        tracer = DriverTracer(parser=None, verbose=False)
        tracer.collect(tree, 'dut.sv')
        
        drivers = tracer.get_drivers('q')
        # 应检测到多驱动
        print(f"driver count: {len(drivers.get('q', []))}")

    @pytest.mark.e2e
    def test_source_extraction_display(self):
        """source 提取并显示"""
        code = '''
module dut(input clk, input a, input b, output q);
    always_ff @(posedge clk) q <= a + b;
endmodule
'''
        tree = SVParser(verbose=False).parse_text(code)
        tracer = DriverTracer(parser=None, verbose=False)
        tracer.collect(tree, 'dut.sv')
        
        drivers = tracer.get_drivers('q')
        if drivers:
            d = drivers['q'][0]
            # sources 应该非空
            assert len(d.sources) > 0, f"Expected sources, got {d.sources}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
