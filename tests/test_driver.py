"""
Driver Tracer 测试
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parse import SVParser
from trace import DriverTracer


def test_assign_driver():
    """测试 assign 驱动"""
    code = '''
module top;
    logic [7:0] data;
    logic [7:0] next_data;
    
    assign data = next_data;
endmodule
'''
    
    parser = SVParser()
    parser.parse_text(code)
    
    tracer = DriverTracer(parser)
    drivers = tracer.find_driver("data")
    
    print(f"Found {len(drivers)} driver(s) for 'data'")
    for d in drivers:
        print(f"  - {d}")
    
    assert len(drivers) >= 1, "Should find at least 1 driver"
    return True


def test_always_ff_driver():
    """测试 always_ff 驱动"""
    code = '''
module top;
    logic clk;
    logic rst_n;
    logic [7:0] counter;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            counter <= 8'd0;
        else
            counter <= counter + 1;
    end
endmodule
'''
    
    parser = SVParser()
    parser.parse_text(code)
    
    tracer = DriverTracer(parser)
    drivers = tracer.find_driver("counter")
    
    print(f"Found {len(drivers)} driver(s) for 'counter'")
    for d in drivers:
        print(f"  - {d}")
    
    return True


def test_if_in_assign():
    """测试 if 内赋值"""
    code = '''
module top;
    logic sel;
    logic [7:0] a;
    logic [7:0] b;
    logic [7:0] out;
    
    assign out = sel ? a : b;
endmodule
'''
    
    parser = SVParser()
    parser.parse_text(code)
    
    tracer = DriverTracer(parser)
    drivers = tracer.find_driver("out")
    
    print(f"Found {len(drivers)} driver(s) for 'out'")
    for d in drivers:
        print(f"  - {d}")
    
    return True


if __name__ == "__main__":
    print("Testing assign driver...")
    test_assign_driver()
    
    print("\nTesting always_ff driver...")
    test_always_ff_driver()
    
    print("\nTesting if in assign...")
    test_if_in_assign()
    
    print("\n✓ All driver tests passed!")


def test_load_tracer():
    """测试 Load 追踪"""
    from trace import LoadTracer
    
    code = '''
module top;
    logic [7:0] a;
    logic [7:0] b;
    logic [7:0] out;
    
    assign out = a + b;
endmodule
'''
    
    parser = SVParser()
    parser.parse_text(code)
    
    tracer = LoadTracer(parser)
    loads = tracer.find_load("a")
    
    print(f"Found {len(loads)} load(s) for 'a'")
    for l in loads:
        print(f"  - {l}")
    
    return True


if __name__ == "__main__":
    print("Testing assign driver...")
    test_assign_driver()
    
    print("\nTesting always_ff driver...")
    test_always_ff_driver()
    
    print("\nTesting if in assign...")
    test_if_in_assign()
    
    print("\nTesting load tracer...")
    test_load_tracer()
    
    print("\n✓ All tests passed!")
