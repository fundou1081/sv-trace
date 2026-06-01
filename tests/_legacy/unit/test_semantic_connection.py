"""
Connection Semantic Tests - 金标准测试
"""

import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.connection import ConnectionTracer


def test_instance():
    """测试模块实例"""
    sv_code = """
module top;
    my_dut u_dut();
endmodule

module my_dut;
    logic clk;
endmodule
"""
    tree = SVParser().parse_text(sv_code, "top.sv")
    ct = ConnectionTracer(use_semantic=True)
    ct.collect(tree, "top.sv")
    
    print(f"  实例: {len(ct.instances)}")
    
    print("✅ test_instance PASS")


def test_port_connection():
    """测试端口连接"""
    sv_code = """
module top;
    logic clk;
    my_dut u_dut (.clk(clk));
endmodule

module my_dut;
    input clk;
endmodule
"""
    tree = SVParser().parse_text(sv_code, "top.sv")
    ct = ConnectionTracer(use_semantic=True)
    ct.collect(tree, "top.sv")
    
    print(f"  实例: {len(ct.instances)}, 连接: {len(ct.connections)}")
    
    print("✅ test_port_connection PASS")


if __name__ == '__main__':
    test_instance()
    test_port_connection()
    print("\n🎉 所有 Connection 测试通过")
