#!/usr/bin/env python3
"""
sv_trace 边界场景测试
"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.driver import DriverTracer
from trace.load import LoadTracer
from trace.connection import ConnectionTracer


# 边界测试用例
EDGE_CASES = [
    # 1. 多驱动检测
    ("multi_driver", '''
module multi_driver;
    logic a, b, r;
    assign r = a;
    assign r = b;
endmodule
'''),
    # 2. 复杂 case 语句
    ("complex_case", '''
module complex_case;
    logic [2:0] sel;
    logic [7:0] a, b, c, d, e, f, g, h, r;
    always_comb begin
        case (sel)
            0: r = a;
            1: r = b;
            2: r = c;
            3: r = d;
            4: r = e;
            5: r = f;
            6: r = g;
            default: r = h;
        endcase
    end
endmodule
'''),
    # 3. 嵌套 if
    ("nested_if", '''
module nested_if;
    logic a, b, c, d, r;
    always_comb begin
        if (a) begin
            if (b)
                r = c;
            else
                r = d;
        end else
            r = 0;
    end
endmodule
'''),
    # 4. always_ff 多个进程
    ("multi_alwaysff", '''
module multi_alwaysff;
    logic clk, rst, a, b, c, d;
    always_ff @(posedge clk) begin
        if (rst) begin
            a <= 0;
        end else begin
            a <= b;
        end
    end
    always_ff @(posedge clk) begin
        c <= d;
    end
endmodule
'''),
    # 5. 函数调用
    ("function_call", '''
module function_call;
    logic [7:0] a, b, r;
    function [7:0] add;
        input [7:0] x, y;
        add = x + y;
    endfunction
    always_comb begin
        r = add(a, b);
    end
endmodule
'''),
]


def test_edge_case(name, code):
    """测试单个边界用例"""
    try:
        parser = SVParser()
        parser.parse_text(code, f"{name}.sv")
        
        drv = DriverTracer(parser)
        drivers = drv.get_drivers('*')
        
        load_tracer = LoadTracer(parser)
        signals = load_tracer.get_all_signals()
        
        conn = ConnectionTracer(parser)
        
        print(f"  ✅ {name}: {len(drivers)} drivers, {len(signals)} signals")
        return True
    except Exception as e:
        print(f"  ❌ {name}: {str(e)[:30]}")
        return False


def main():
    print("=" * 60)
    print("sv_trace 边界场景测试")
    print("=" * 60)
    
    passed = 0
    for name, code in EDGE_CASES:
        if test_edge_case(name, code):
            passed += 1
    
    print("=" * 60)
    print(f"结果: {passed}/{len(EDGE_CASES)} 通过")
    print("=" * 60)
    
    return passed == len(EDGE_CASES)


if __name__ == '__main__':
    main()
