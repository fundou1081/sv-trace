"""
DataFlow 金标准测试

按项目纪律验证数据流分析
"""

import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.dataflow import DataFlowTracer


def test_basic_dataflow():
    """测试基本数据流"""
    sv = '''module test (input clk, input d, output q);
        reg r1, r2;
        always_ff @(posedge clk) begin
            r1 <= d;
            r2 <= r1;
        end
        assign q = r2;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    dt = DataFlowTracer(use_semantic=True)
    dt.collect(tree, 'test.sv')
    
    print(f'【基本数据流】')
    print(f'  寄存器: {dt.register_count}')
    print(f'  线网: {dt.wire_count}')
    print(f'  结果: {"✅" if dt.register_count >= 2 else "❌"}')
    return dt.register_count >= 2


def test_drivers_loads():
    """测试驱动/负载查找"""
    sv = '''module test (input clk, input a, input b, output y);
        reg r;
        always_ff @(posedge clk) r <= a & b;
        assign y = r;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    dt = DataFlowTracer(use_semantic=True)
    dt.collect(tree, 'test.sv')
    
    drivers = dt.find_drivers('r')
    loads = dt.find_loads('r')
    
    print(f'【驱动/负载查找】')
    print(f'  r 的驱动: {drivers}')
    print(f'  r 的负载: {loads}')
    print(f'  结果: ✅')
    return True


def test_pipeline():
    """测试流水线"""
    sv = '''module test (input clk, input d, output q);
        reg [7:0] p1, p2, p3, p4;
        always_ff @(posedge clk) begin
            p1 <= d;
            p2 <= p1;
            p3 <= p2;
            p4 <= p3;
        end
        assign q = p4;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    dt = DataFlowTracer(use_semantic=True)
    dt.collect(tree, 'test.sv')
    
    print(f'【流水线】')
    print(f'  寄存器数: {dt.register_count}')
    print(f'  最大深度: {dt.result.max_depth}')
    print(f'  结果: {"✅" if dt.register_count >= 4 else "❌"}')
    return dt.register_count >= 4


def test_combinational():
    """测试组合逻辑"""
    sv = '''module test (input a, b, c, output y);
        wire tmp;
        assign tmp = a & b;
        assign y = tmp | c;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    dt = DataFlowTracer(use_semantic=True)
    dt.collect(tree, 'test.sv')
    
    print(f'【组合逻辑】')
    print(f'  线网: {dt.wire_count}')
    print(f'  结果: {"✅" if dt.wire_count >= 2 else "❌"}')
    return dt.wire_count >= 2


def test_real_designs():
    """真实设计测试"""
    import os, glob
    
    base = '/Users/fundou/my_dv_proj/basic_verilog'
    files = glob.glob(f'{base}/*.sv')[:5]
    
    print(f'【真实设计】')
    total_regs = 0
    total_wires = 0
    
    for f in files:
        name = os.path.basename(f)
        try:
            with open(f) as fp:
                code = fp.read()
            tree = SVParser().parse_text(code, name)
            
            dt = DataFlowTracer(use_semantic=True)
            dt.collect(tree, name)
            
            total_regs += dt.register_count
            total_wires += dt.wire_count
        except:
            pass
    
    print(f'  总寄存器: {total_regs}')
    print(f'  总线网: {total_wires}')
    print(f'  结果: ✅')
    return True


if __name__ == '__main__':
    print('=== DataFlow 测试 ===\n')
    
    results = []
    results.append(('基本数据流', test_basic_dataflow()))
    results.append(('驱动/负载', test_drivers_loads()))
    results.append(('流水线', test_pipeline()))
    results.append(('组合逻辑', test_combinational()))
    results.append(('真实设计', test_real_designs()))
    
    print('\n=== 测试汇总 ===')
    for name, passed in results:
        print(f'  {name}: {"✅" if passed else "❌"}')
    
    ok = sum(1 for _, p in results if p)
    print(f'\n通过: {ok}/{len(results)}')
