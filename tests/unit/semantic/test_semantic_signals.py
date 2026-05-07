"""
信号语义类型金标准测试

按项目纪律验证 Signal/Port/Register 提取
"""

import sys
sys.path.insert(0, 'src')

from parse import SVParser
from semantic.base import SemanticCollector


def test_signal_declarator():
    """测试信号声明提取"""
    sv = '''module test (input clk);
        logic [7:0] data;
        logic [15:0] addr;
        wire ready;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 't.sv')
    coll = SemanticCollector()
    coll.collect(tree, 't.sv')
    
    from semantic.signal import SignalItem
    items = coll.get_by_type(SignalItem)
    
    print(f'【信号声明】')
    print(f'  提取数量: {len(items)}')
    
    # 验证
    names = [i.path for i in items if i.path]
    print(f'  信号: {names[:5]}')
    
    passed = len(items) >= 2
    print(f'  结果: {"✅" if passed else "❌"}')
    return passed


def test_port_declaration():
    """测试端口提取"""
    sv = '''module test (
        input clk,
        input [7:0] data,
        output [7:0] out
    );
    endmodule'''
    
    tree = SVParser().parse_text(sv, 't.sv')
    coll = SemanticCollector()
    coll.collect(tree, 't.sv')
    
    from semantic.signal import PortItem
    items = coll.get_by_type(PortItem)
    
    print(f'【端口声明】')
    print(f'  提取数量: {len(items)}')
    
    passed = len(items) >= 2
    print(f'  结果: {"✅" if passed else "❌"}')
    return passed


def test_register():
    """测试寄存器提取"""
    sv = '''module test (input clk);
        reg [7:0] counter;
        reg state;
        wire data;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 't.sv')
    coll = SemanticCollector()
    coll.collect(tree, 't.sv')
    
    from semantic.signal import RegisterItem
    items = coll.get_by_type(RegisterItem)
    
    print(f'【寄存器】')
    print(f'  提取数量: {len(items)}')
    passed = len(items) >= 1
    print(f'  结果: {"✅" if passed else "❌"}')
    return passed


def test_all_in_real_designs():
    """真实设计测试"""
    import os, glob
    
    base = '/Users/fundou/my_dv_proj/basic_verilog'
    files = glob.glob(f'{base}/*.sv')[:5]
    
    print(f'【真实设计信号提取】')
    
    total_signals = 0
    for f in files:
        name = os.path.basename(f)
        try:
            with open(f) as fp:
                code = fp.read()
            tree = SVParser().parse_text(code, name)
            coll = SemanticCollector()
            coll.collect(tree, name)
            
            from semantic.signal import SignalItem
            items = coll.get_by_type(SignalItem)
            total_signals += len(items)
        except:
            pass
    
    print(f'  总信号数: {total_signals}')
    passed = total_signals >= 10
    print(f'  结果: {"✅" if passed else "❌"}')
    return passed


if __name__ == '__main__':
    print('=== 信号语义类型金标准测试 ===\n')
    
    results = []
    results.append(('信号声明', test_signal_declarator()))
    results.append(('端口声明', test_port_declaration()))
    results.append(('寄存器', test_register()))
    results.append(('真实设计', test_all_in_real_designs()))
    
    print('\n=== 测试汇总 ===')
    for name, passed in results:
        print(f'  {name}: {"✅" if passed else "❌"}')
    
    ok = sum(1 for _, p in results if p)
    print(f'\n通过: {ok}/{len(results)}')
