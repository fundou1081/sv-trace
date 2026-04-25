"""LoadTracer 边界测试用例"""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from parse import SVParser
from trace.load import LoadTracer

def test_load_edge_cases():
    """边界测试: LoadTracer"""
    results = {}
    
    # 1. 多维数组的加载
    code1 = '''module edge_mem_load;
        logic [7:0] mem [0:15][0:15];
        logic [3:0] i, j;
        logic [7:0] data;
        always_comb
            data = mem[i][j];
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code1)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        lt = LoadTracer(parser)
        loads = lt.find_load('mem')
        results['multi_dim_array'] = len(loads)
    finally:
        os.unlink(tmp)
    
    # 2. 嵌套表达式中的加载
    code2 = '''module edge_nested_expr;
        logic [7:0] a, b, c, r;
        always_comb
            r = (a + b) * c;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code2)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        lt = LoadTracer(parser)
        loads = lt.find_load('a')
        results['nested_expr'] = len(loads)
    finally:
        os.unlink(tmp)
    
    # 3. for 循环中的加载
    code3 = '''module edge_for_loop_load;
        logic [7:0] cnt;
        logic clk;
        logic [3:0] i;
        always_ff @(posedge clk) begin
            for (i = 0; i < 10; i = i + 1) begin
                cnt <= cnt + 1;
            end
        end
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code3)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        lt = LoadTracer(parser)
        loads = lt.find_load('cnt')
        results['for_loop'] = len(loads)
    finally:
        os.unlink(tmp)
    
    # 4. 三元表达式中的加载
    code4 = '''module edge_ternary_load;
        logic [7:0] a, b, sel, r;
        always_comb
            r = sel ? a : b;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code4)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        lt = LoadTracer(parser)
        loads = lt.find_load('a')
        results['ternary'] = len(loads)
    finally:
        os.unlink(tmp)
    
    # 5. generate for 中的加载
    code5 = '''module edge_gen_for_load;
        parameter N = 4;
        logic [7:0] data_in [0:N-1];
        logic [7:0] data_out;
        genvar i;
        generate
            for (i = 0; i < N; i = i + 1) begin : gen_loop
                always_comb
                    data_out = data_in[i];
            end
        endgenerate
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code5)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        lt = LoadTracer(parser)
        loads = lt.find_load('data_in')
        results['gen_for'] = len(loads)
    finally:
        os.unlink(tmp)
    
    # 6. 函数参数中的加载
    code6 = '''module edge_func_param_load;
        logic [7:0] a, b;
        logic [7:0] result;
        function [7:0] my_func;
            input [7:0] x, y;
            input [7:0] sel;
            my_func = sel ? x : y;
        endfunction
        always_comb
            result = my_func(a, b, 8'hFF);
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code6)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        lt = LoadTracer(parser)
        loads = lt.find_load('a')
        results['func_param'] = len(loads)
    finally:
        os.unlink(tmp)
    
    # 7. 重复信号在右侧
    code7 = '''module edge_repeated_signal;
        logic [7:0] a;
        logic [7:0] r1, r2;
        always_comb begin
            r1 = a + a;
            r2 = a * 2;
        end
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code7)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        lt = LoadTracer(parser)
        loads = lt.find_load('a')
        results['repeated_signal'] = len(loads)
    finally:
        os.unlink(tmp)
    
    # 8. 位选择作为加载
    code8 = '''module edge_bit_select_load;
        logic [7:0] data;
        logic [2:0] idx;
        logic bit_val;
        always_comb
            bit_val = data[idx];
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code8)
        tmp = f.name
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        lt = LoadTracer(parser)
        loads = lt.find_load('data')
        results['bit_select_load'] = len(loads)
    finally:
        os.unlink(tmp)
    
    return results


if __name__ == '__main__':
    print("=== LoadTracer Edge Cases ===")
    results = test_load_edge_cases()
    for name, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"{status} {name}: {count} loads")
    
    passed = sum(1 for c in results.values() if c > 0)
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({100*passed//total}%)")
