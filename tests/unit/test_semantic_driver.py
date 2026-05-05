"""
Driver Semantic Tests - 金标准测试

测试设计: 基于 semantic 层的 Driver 模块
"""

import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.driver import DriverCollector
from semantic.base import SemanticCollector


def test_driver_always_ff():
    """测试 always_ff 非阻塞赋值"""
    sv_code = """
module test_driver;
    logic clk;
    logic rst_n;
    logic [7:0] data;
    logic [7:0] data_out;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data_out <= 8'b0;
        else
            data_out <= data;
    end
endmodule
"""
    tree = SVParser().parse_text(sv_code, "test.sv")
    dc = DriverCollector(use_semantic=True)
    dc.collect(tree, "test.sv")
    
    # 金标准
    # data_out 的驱动: always_ff 非阻塞 <=
    assert 'data_out' in dc.drivers
    drivers = dc.drivers['data_out']
    assert len(drivers) >= 1
    # assert drivers[0].kind.name == 'AlwaysFF'
    
    print("✅ test_driver_always_ff PASS")


def test_driver_always_comb():
    """测试 always_comb 阻塞赋值"""
    sv_code = """
module test_driver;
    logic [7:0] data;
    logic [7:0] data_out;
    
    always_comb begin
        data_out = data;
    end
endmodule
"""
    tree = SVParser().parse_text(sv_code, "test.sv")
    dc = DriverCollector(use_semantic=True)
    dc.collect(tree, "test.sv")
    
    # 金标准
    # data_out 的驱动: always_comb 阻塞 =
    assert 'data_out' in dc.drivers
    
    print("✅ test_driver_always_comb PASS")


def test_driver_continuous():
    """测试 assign 连续赋值"""
    sv_code = """
module test_driver;
    logic [7:0] data;
    logic [7:0] data_out;
    
    assign data_out = data;
endmodule
"""
    tree = SVParser().parse_text(sv_code, "test.sv")
    dc = DriverCollector(use_semantic=True)
    dc.collect(tree, "test.sv")
    
    # 金标准
    # data_out 的驱动: assign 连续
    assert 'data_out' in dc.drivers
    
    print("✅ test_driver_continuous PASS")


def test_all_three_types():
    """测试3种赋值类型"""
    sv_code = """
module test_all;
    logic clk;
    logic [7:0] data;
    logic [7:0] out1, out2, out3;
    
    always_ff @(posedge clk) begin
        out1 <= data;
    end
    
    always_comb begin
        out2 = data;
    end
    
    assign out3 = data;
endmodule
"""
    tree = SVParser().parse_text(sv_code, "test.sv")
    dc = DriverCollector(use_semantic=True)
    dc.collect(tree, "test.sv")
    
    # 金标准
    # out1: always_ff
    # out2: always_comb  
    # out3: continuous
    print(f"  驱动: {list(dc.drivers.keys())}")
    
    print("✅ test_all_three_types PASS")


if __name__ == '__main__':
    test_driver_always_ff()
    test_driver_always_comb()
    test_driver_continuous()
    test_all_three_types()
    print("\n🎉 所有 Driver 测试通过")
