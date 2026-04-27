"""测试端口方向和跨模块追踪"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parse import SVParser
from query.hierarchy import HierarchicalResolver

TEST_CODE = """
module top;
    logic [7:0] data;
    logic [7:0] result;
    logic enable;
    logic clk;
    
    cpu u_cpu (.clk(clk), .data_in(data), .result(result), .enable(enable));
endmodule

module cpu (input clk, input [7:0] data_in, output [7:0] result, input enable);
    logic [7:0] reg_data;
    always_ff @(posedge clk) if (enable) reg_data <= data_in;
    assign result = reg_data;
endmodule
"""

def test():
    parser = SVParser()
    parser.parse_text(TEST_CODE, "test.sv")
    
    resolver = HierarchicalResolver(parser)
    
    # 1. 实例带端口方向
    print("=== Instances with Direction ===")
    instances = resolver.get_all_instances()
    for inst in instances:
        print(f"  {inst['instance_name']} ({inst['module_type']})")
        for p in inst.get('ports', []):
            print(f"    {p['port']}: {p['direction']} -> {p['connected_to']}")
    
    # 2. 简单信号
    print("\n=== Simple Signal (port) ===")
    result = resolver.resolve_signal("result")
    print(f"  result: type={result['type'] if result else 'N/A'}, direction={result.get('direction') if result else 'N/A'}")
    
    # 3. 层级信号
    print("\n=== Hierarchy Signal ===")
    result = resolver.resolve_signal("top.u_cpu.reg_data")
    print(f"  top.u_cpu.reg_data: module={result['module'] if result else 'None'}")

test()
