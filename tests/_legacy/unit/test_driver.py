"""
DriverTracer & LoadTracer 完整测试
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parse import SVParser
from trace import DriverTracer, LoadTracer


def test_case(name, code, signal, expect_driver=True, expect_load=False):
    """通用测试用例"""
    print(f"\n--- {name} ---")
    print(f"Code: {code[:50]}...")
    print(f"Signal: {signal}")
    
    parser = SVParser()
    parser.parse_text(code)
    
    # Driver 测试
    if expect_driver:
        driver_tracer = DriverTracer(parser)
        drivers = driver_tracer.find_driver(signal)
        print(f"Drivers found: {len(drivers)}")
        for d in drivers:
            print(f"  - {d.kind.name}: {d.source_expr[:30] if d.source_expr else '(none)'}")
    
    # Load 测试
    if expect_load:
        load_tracer = LoadTracer(parser)
        loads = load_tracer.find_load(signal)
        print(f"Loads found: {len(loads)}")
        for l in loads:
            print(f"  - {l.context[:30] if l.context else '(none)'}")
    
    return True


# ========== Driver 测试 ==========

def test_driver_assign():
    """assign 驱动"""
    code = '''module top; logic [7:0] data; assign data = 8'hFF; endmodule'''
    return test_case("assign driver", code, "data", expect_driver=True)


def test_driver_assign_expr():
    """assign 表达式"""
    code = '''module top; logic [7:0] a, b, c; assign c = a + b; endmodule'''
    return test_case("assign expr", code, "c", expect_driver=True)


def test_driver_assign_with_select():
    """assign 位选"""
    code = '''module top; logic [7:0] data; logic [2:0] idx; assign data[idx] = 1'b1; endmodule'''
    return test_case("assign select", code, "data", expect_driver=True)


def test_driver_always_ff():
    """always_ff 驱动"""
    code = '''module top; logic clk; logic [7:0] cnt; always_ff @(posedge clk) cnt <= cnt + 1; endmodule'''
    return test_case("always_ff", code, "cnt", expect_driver=True)


def test_driver_always_ff_async_reset():
    """always_ff 异步复位"""
    code = '''module top; logic clk, rst_n; logic [7:0] cnt; always_ff @(posedge clk or negedge rst_n) if (!rst_n) cnt <= 0; else cnt <= cnt + 1; endmodule'''
    return test_case("always_ff async reset", code, "cnt", expect_driver=True)


def test_driver_always_comb():
    """always_comb 驱动"""
    code = '''module top; logic [7:0] a, b, max; always_comb max = (a > b) ? a : b; endmodule'''
    return test_case("always_comb", code, "max", expect_driver=True)


def test_driver_always_latch():
    """always_latch 驱动"""
    code = '''module top; logic [7:0] data; logic en; always_latch if (en) data <= data + 1; endmodule'''
    return test_case("always_latch", code, "data", expect_driver=True)


def test_driver_multi_assign():
    """多重赋值"""
    code = '''module top; logic [7:0] data; logic sel; assign data = sel ? 8'hFF : 8'h00; endmodule'''
    return test_case("multi assign", code, "data", expect_driver=True)


# ========== Load 测试 ==========

def test_load_in_assign():
    """assign 中的加载"""
    code = '''module top; logic [7:0] a, b, c; assign c = a + b; endmodule'''
    return test_case("load in assign", code, "a", expect_driver=False, expect_load=True)


def test_load_in_if():
    """if 条件中的加载"""
    code = '''module top; logic a, b; logic [7:0] out; assign out = a ? b : 8'h00; endmodule'''
    return test_case("load in if", code, "a", expect_driver=False, expect_load=True)


def test_load_in_case():
    """case 中的加载"""
    code = '''module top; logic [1:0] sel; logic [7:0] out; always_comb case (sel) 2'd0: out = 8'hAA; 2'd1: out = 8'h55; default: out = 8'h00; endcase'''
    return test_case("load in case", code, "sel", expect_driver=False, expect_load=True)


# ========== 边界测试 ==========

def test_no_driver():
    """无驱动"""
    code = '''module top; logic [7:0] data; endmodule'''
    return test_case("no driver", code, "data", expect_driver=True)


def test_no_signal():
    """不存在的信号"""
    code = '''module top; logic [7:0] data; assign data = 8'hFF; endmodule'''
    return test_case("no signal", code, "not_exist", expect_driver=True)


def test_module_signal():
    """跨模块信号名"""
    code = '''module top; logic clk; endmodule'''
    return test_case("module signal", code, "clk", expect_driver=True)


# ========== 运行所有测试 ==========

if __name__ == "__main__":
    tests = [
        # Driver tests
        ("test_driver_assign", test_driver_assign),
        ("test_driver_assign_expr", test_driver_assign_expr),
        ("test_driver_assign_with_select", test_driver_assign_with_select),
        ("test_driver_always_ff", test_driver_always_ff),
        ("test_driver_always_ff_async_reset", test_driver_always_ff_async_reset),
        ("test_driver_always_comb", test_driver_always_comb),
        ("test_driver_always_latch", test_driver_always_latch),
        ("test_driver_multi_assign", test_driver_multi_assign),
        # Load tests
        ("test_load_in_assign", test_load_in_assign),
        ("test_load_in_if", test_load_in_if),
        ("test_load_in_case", test_load_in_case),
        # Edge cases
        ("test_no_driver", test_no_driver),
        ("test_no_signal", test_no_signal),
        ("test_module_signal", test_module_signal),
    ]
    
    passed = 0
    failed = 0
    
    for name, test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All tests passed!")
    else:
        print(f"✗ {failed} tests failed")
