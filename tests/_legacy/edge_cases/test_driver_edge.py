"""DriverCollector 边界测试用例"""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from parse import SVParser
from trace.driver import DriverCollector

def test_driver_edge_cases():
    """边界测试: DriverCollector"""
    results = {}
    
    # 1. 连续赋值中的数组下标
    code1 = '''module edge_array_index;
        logic [7:0] mem [0:15];
        logic [3:0] idx;
        logic [7:0] data;
        assign mem[idx] = data;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code1)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        dc = DriverCollector(parser)
        drivers = dc.find_driver('mem')
        results['array_index_assign'] = len(drivers)
    finally:
        os.unlink(tmp)
    
    # 2. generate if 中的驱动
    code2 = '''module edge_gen_if;
        parameter USE_ALT = 0;
        logic [7:0] a, b, c;
        generate
            if (USE_ALT == 1)
                assign c = a + 1;
            else
                assign c = b + 1;
        endgenerate
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code2)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        dc = DriverCollector(parser)
        drivers = dc.find_driver('c')
        results['gen_if'] = len(drivers)
    finally:
        os.unlink(tmp)
    
    # 3. 多个 always 块驱动同一信号 (应该被检测)
    code3 = '''module edge_multi_always;
        logic [7:0] a, b, c, r;
        logic cond1, cond2;
        always_comb begin
            if (cond1)
                r = a;
        end
        always_comb begin
            if (cond2)
                r = b;
        end
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code3)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        dc = DriverCollector(parser)
        drivers = dc.find_driver('r')
        results['multi_always'] = len(drivers)
    finally:
        os.unlink(tmp)
    
    # 4. 函数调用中的驱动
    code4 = '''module edge_func_call;
        logic [7:0] a, b, result;
        function [7:0] add;
            input [7:0] x, y;
            add = x + y;
        endfunction
        assign result = add(a, b);
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code4)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        dc = DriverCollector(parser)
        drivers = dc.find_driver('result')
        results['func_call'] = len(drivers)
    finally:
        os.unlink(tmp)
    
    # 5. 位选择赋值
    code5 = '''module edge_bit_select;
        logic [7:0] data;
        logic [2:0] idx;
        logic bit_val;
        assign data[idx] = bit_val;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code5)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        dc = DriverCollector(parser)
        drivers = dc.find_driver('data')
        results['bit_select'] = len(drivers)
    finally:
        os.unlink(tmp)
    
    # 6. 阻塞赋值在 always_ff 中
    code6 = '''module edge_blocking_ff;
        logic clk, rst;
        logic [7:0] data, r;
        always_ff @(posedge clk) begin
            if (rst)
                r = 0;
            else
                r = data;  // 阻塞赋值 - 可能是 bug
        end
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code6)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        dc = DriverCollector(parser)
        drivers = dc.find_driver('r')
        results['blocking_ff'] = len(drivers)
    finally:
        os.unlink(tmp)
    
    # 7. 隐式端口连接
    code7 = '''module edge_implicit_port (
        input [7:0] a,
        output [7:0] b
    );
        assign b = a + 1;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code7)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        dc = DriverCollector(parser)
        drivers = dc.find_driver('b')
        results['implicit_port'] = len(drivers)
    finally:
        os.unlink(tmp)
    
    # 8. 条件编译中的驱动
    code8 = '''module edge_ifdef;
        `ifdef USE_ALT
            logic [7:0] c;
            assign c = 8'hFF;
        `else
            logic [7:0] c;
            assign c = 8'h00;
        `endif
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code8)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        dc = DriverCollector(parser)
        drivers = dc.find_driver('c')
        results['ifdef'] = len(drivers)
    finally:
        os.unlink(tmp)
    
    return results


if __name__ == '__main__':
    print("=== DriverCollector Edge Cases ===")
    results = test_driver_edge_cases()
    for name, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"{status} {name}: {count} drivers")
    
    # 汇总
    passed = sum(1 for c in results.values() if c > 0)
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({100*passed//total}%)")
