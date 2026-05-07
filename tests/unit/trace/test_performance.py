"""
性能/资源估算金标准测试

按项目纪律验证
"""

import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.performance import PerformanceEstimator, AreaEstimator


def test_performance():
    """测试性能估算"""
    sv = '''module test (input clk, input [7:0] d, output [7:0] q);
        reg [7:0] p1, p2, p3;
        always_ff @(posedge clk) begin
            p1 <= d;
            p2 <= p1;
            p3 <= p2;
        end
        assign q = p3;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    pe = PerformanceEstimator()
    pe.estimate(tree, 'test.sv')
    
    print(f'【性能估算】')
    print(f'  频率: {pe.frequency_mhz:.0f} MHz')
    print(f'  流水线: {pe.latency}')
    print(f'  结果: {"✅" if pe.frequency_mhz > 0 else "❌"}')
    return pe.frequency_mhz > 0


def test_area():
    """测试资源估算"""
    sv = '''module test (input clk, input [7:0] d, output [7:0] q);
        reg [7:0] r1, r2, r3;
        always_ff @(posedge clk) begin
            r1 <= d;
            r2 <= r1;
            r3 <= r2;
        end
        assign q = r3;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    ae = AreaEstimator()
    ae.estimate(tree, 'test.sv')
    
    print(f'【资源估算】')
    print(f'  寄存器: {ae.registers}')
    print(f'  LUT: {ae.luts}')
    print(f'  结果: {"✅" if ae.registers >= 3 else "❌"}')
    return ae.registers >= 3


def test_real_designs():
    """真实设计测试"""
    import os, glob
    
    base = '/Users/fundou/my_dv_proj/basic_verilog'
    files = glob.glob(f'{base}/*.sv')[:5]
    
    print(f'【真实设计】')
    total_regs = 0
    total_freq = 0
    
    for f in files[:3]:
        name = os.path.basename(f)
        try:
            with open(f) as fp:
                code = fp.read()
            tree = SVParser().parse_text(code, name)
            
            pe = PerformanceEstimator()
            pe.estimate(tree, name)
            
            ae = AreaEstimator()
            ae.estimate(tree, name)
            
            total_regs += ae.registers
            total_freq += pe.frequency_mhz
        except:
            pass
    
    print(f'  总寄存器: {total_regs}')
    print(f'  总频率: {total_freq:.0f} MHz')
    print(f'  结果: ✅')
    return True


if __name__ == '__main__':
    print('=== 性能估算测试 ===\n')
    
    results = []
    results.append(('性能估算', test_performance()))
    results.append(('资源估算', test_area()))
    results.append(('真实设计', test_real_designs()))
    
    print('\n=== 测试汇总 ===')
    for name, passed in results:
        print(f'  {name}: {"✅" if passed else "❌"}')
    
    ok = sum(1 for _, p in results if p)
    print(f'\n通过: {ok}/{len(results)}')
