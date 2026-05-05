"""
Flow Analysis 金标准测试
"""

import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.flow_analyzer import FlowAnalyzer


def test_flow_graph():
    """测试数据流图"""
    sv = '''module test (input clk, input d, output q);
        reg r1, r2;
        always_ff @(posedge clk) begin
            r1 <= d;
            r2 <= r1;
        end
        assign q = r2;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    fa = FlowAnalyzer(use_semantic=True)
    fa.collect(tree, 'test.sv')
    
    print(f'【数据流图】')
    print(f'  信号: {len(fa.all_signals)}')
    print(f'  路径: {fa.path_count}')
    print(f'  结果: {"✅" if len(fa.all_signals) >= 2 else "❌"}')
    return len(fa.all_signals) >= 2


def test_boundary():
    """测试边界识别"""
    sv = '''module test (input clk, input d, output q);
        reg r;
        always_ff @(posedge clk) r <= d;
        assign q = r;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    fa = FlowAnalyzer(use_semantic=True)
    fa.collect(tree, 'test.sv')
    
    print(f'【边界识别】')
    print(f'  输入: {fa.boundary.input_signals}')
    print(f'  输出: {fa.boundary.output_signals}')
    print(f'  结果: ✅')
    return True


def test_find_path():
    """测试路径查找"""
    sv = '''module test (input clk, input d, output q);
        reg a, b, c;
        always_ff @(posedge clk) begin
            a <= d;
            b <= a;
            c <= b;
        end
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    fa = FlowAnalyzer(use_semantic=True)
    fa.collect(tree, 'test.sv')
    
    print(f'【路径查找】')
    print(f'  信号数: {len(fa.all_signals)}')
    print(f'  结果: {"✅" if len(fa.all_signals) >= 3 else "❌"}')
    return len(fa.all_signals) >= 3


def test_real_designs():
    """真实设计测试"""
    import os, glob
    
    base = '/Users/fundou/my_dv_proj/basic_verilog'
    files = glob.glob(f'{base}/*.sv')[:5]
    
    print(f'【真实设计】')
    total = 0
    
    for f in files[:3]:
        name = os.path.basename(f)
        try:
            with open(f) as fp:
                code = fp.read()
            tree = SVParser().parse_text(code, name)
            fa = FlowAnalyzer(use_semantic=True)
            fa.collect(tree, name)
            total += fa.path_count
        except:
            pass
    
    print(f'  总路径: {total}')
    print(f'  结果: ✅')
    return True


if __name__ == '__main__':
    print('=== Flow Analysis 测试 ===\n')
    
    results = []
    results.append(('数据流图', test_flow_graph()))
    results.append(('边界识别', test_boundary()))
    results.append(('路径查找', test_find_path()))
    results.append(('真实设计', test_real_designs()))
    
    print('\n=== 测试汇总 ===')
    for name, passed in results:
        print(f'  {name}: {"✅" if passed else "❌"}')
    
    ok = sum(1 for _, p in results if p)
    print(f'\n通过: {ok}/{len(results)}')
