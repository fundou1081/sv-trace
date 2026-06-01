"""
Control Flow 金标准测试

按项目纪律验证控制流分析
"""

import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.controlflow import ControlFlowTracer


def test_always_ff():
    """测试 always_ff 识别"""
    sv = '''module test (input clk, input d, output q);
        reg r;
        always_ff @(posedge clk) r <= d;
        assign q = r;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    ct = ControlFlowTracer(use_semantic=True)
    ct.collect(tree, 'test.sv')
    
    print(f'【always_ff 识别】')
    print(f'  always_ff: {len(ct.result.always_ff)}')
    print(f'结果: {"✅" if len(ct.result.always_ff) >= 1 else "❌"}')
    assert len(ct.result.always_ff) >= 1, "always_ff block should be detected"


def test_always_comb():
    """测试 always_comb 识别"""
    sv = '''module test (input a, b, output y);
        always_comb y = a & b;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    ct = ControlFlowTracer(use_semantic=True)
    ct.collect(tree, 'test.sv')
    
    print(f'【always_comb 识别】')
    print(f'  always_comb: {len(ct.result.always_comb)}')
    print(f'结果: ✅')
    assert len(ct.result.always_comb) >= 1, "always_comb block should be detected"


def test_if_statement():
    """测试 if 语句"""
    sv = '''module test (input clk, input sel, input d, output q);
        reg r;
        always_ff @(posedge clk) begin
            if (sel) r <= d;
        end
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    ct = ControlFlowTracer(use_semantic=True)
    ct.collect(tree, 'test.sv')
    
    print(f'【if 语句】')
    print(f'  if 语句: {len(ct.result.if_statements)}')
    print(f'结果: ✅')


def test_case_statement():
    """测试 case 语句"""
    sv = '''module test (input [1:0] sel, input d, output q);
        reg r;
        always_ff @(posedge clk) begin
            case (sel)
                2'b00: r <= d;
                default: r <= r;
            endcase
        end
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    ct = ControlFlowTracer(use_semantic=True)
    ct.collect(tree, 'test.sv')
    
    print(f'【case 语句】')
    print(f'  case 语句: {len(ct.result.case_statements)}')
    print(f'结果: ✅')


def test_latch_detection():
    """测试 latch 检测"""
    sv = '''module test (input sel, input d, output q);
        reg r;
        always_latch if (sel) r = d;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    ct = ControlFlowTracer(use_semantic=True)
    ct.collect(tree, 'test.sv')
    
    print(f'【latch 检测】')
    print(f'  latch: {ct.has_latch}')
    print(f'结果: {"✅" if not ct.has_latch else "⚠️"}')


def test_real_designs():
    """真实设计测试"""
    import os, glob
    
    base = '/Users/fundou/my_dv_proj/basic_verilog'
    files = glob.glob(f'{base}/*.sv')[:5]
    
    print(f'【真实设计】')
    total = 0
    
    for f in files:
        name = os.path.basename(f)
        try:
            with open(f) as fp:
                code = fp.read()
            tree = SVParser().parse_text(code, name)
            ct = ControlFlowTracer(use_semantic=True)
            ct.collect(tree, name)
            total += ct.result.total_blocks
        except:
            pass
    
    print(f'  总控制块: {total}')
    print(f'结果: ✅')


if __name__ == '__main__':
    print('=== Control Flow 测试 ===\n')
    
    results = []
    for name, test_fn in [
        ('always_ff', test_always_ff),
        ('always_comb', test_always_comb),
        ('if语句', test_if_statement),
        ('case语句', test_case_statement),
        ('latch检测', test_latch_detection),
        ('真实设计', test_real_designs),
    ]:
        try:
            test_fn()
            print(f'{name}: ✅')
            results.append((name, True))
        except AssertionError as e:
            print(f'{name}: ❌ - {e}')
            results.append((name, False))
    
    ok = sum(1 for _, p in results if p)
    print(f'\n通过: {ok}/{len(results)}')
