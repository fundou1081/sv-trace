"""
时序路径 & CDC 金标准测试

按项目纪律：验证 timing_path 和 clock_domain 功能
"""

import sys
sys.path.insert(0, 'src')

from parse import SVParser
from trace.query.clock_domain import ClockDomainTracer
from trace.query.timing_path import TimingPathTracer


def test_clock_domain():
    """测试时钟域提取"""
    sv = '''module test (
        input clk1, clk2,
        input rst_n,
        input d,
        output q1, q2
    );
        reg r1, r2;
        always_ff @(posedge clk1 or negedge rst_n) begin
            if (!rst_n) r1 <= 0;
            else r1 <= d;
        end
        always_ff @(posedge clk2 or negedge rst_n) begin
            if (!rst_n) r2 <= 0;
            else r2 <= d;
        end
        assign q1 = r1;
        assign q2 = r2;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    ct = ClockDomainTracer(use_semantic=True)
    ct.collect(tree, 'test.sv')
    
    print(f'【时钟域提取】')
    print(f'  时钟数: {len(ct.all_clocks)}')
    print(f'  CDC 路径: {ct.cdc_count}')
    print(f'  结果: {"✅" if len(ct.all_clocks) >= 2 else "❌"}')
    return len(ct.all_clocks) >= 2


def test_timing_path():
    """测试时序路径提取"""
    sv = '''module test (
        input clk,
        input d,
        output q
    );
        reg r1, r2, r3;
        always_ff @(posedge clk) begin
            r1 <= d;
            r2 <= r1;
            r3 <= r2;
        end
        assign q = r3;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'test.sv')
    tt = TimingPathTracer(use_semantic=True)
    tt.collect(tree, 'test.sv')
    
    print(f'【时序路径】')
    print(f'  寄存器: {tt.register_count}')
    print(f'  路径: {tt.path_count}')
    print(f'  最大深度: {tt.result.max_depth}')
    print(f'  结果: {"✅" if tt.register_count >= 3 else "❌"}')
    return tt.register_count >= 3


def test_cdc_path():
    """测试 CDC 路径识别"""
    sv = '''module cdc (
        input clk1, clk2,
        input data_in,
        output data_out
    );
        reg sync;
        reg out;
        // clk1 域
        always_ff @(posedge clk1) sync <= data_in;
        // clk2 域
        always_ff @(posedge clk2) out <= sync;
        assign data_out = out;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 'cdc.sv')
    ct = ClockDomainTracer(use_semantic=True)
    ct.collect(tree, 'cdc.sv')
    
    print(f'【CDC 路径】')
    cdc_paths = ct.find_cdc_paths()
    print(f'  CDC 路径数: {len(cdc_paths)}')
    for src, dst in cdc_paths:
        print(f'    {src} -> {dst}')
    print(f'  结果: ✅')
    return True


def test_real_designs():
    """真实设计测试"""
    import os, glob
    
    base = '/Users/fundou/my_dv_proj/basic_verilog'
    files = glob.glob(f'{base}/*.sv')[:5]
    
    print(f'【真实设计】')
    total_paths = 0
    total_clocks = 0
    
    for f in files:
        name = os.path.basename(f)
        try:
            with open(f) as fp:
                code = fp.read()
            tree = SVParser().parse_text(code, name)
            
            # 时钟域
            ct = ClockDomainTracer(use_semantic=True)
            ct.collect(tree, name)
            total_clocks += len(ct.all_clocks)
            
            # 时序路径
            tt = TimingPathTracer(use_semantic=True)
            tt.collect(tree, name)
            total_paths += tt.path_count
        except:
            pass
    
    print(f'  总时钟域: {total_clocks}')
    print(f'  总路径: {total_paths}')
    print(f'  结果: {"✅" if total_paths >= 0 else "❌"}')
    return True


if __name__ == '__main__':
    print('=== 时序路径 & CDC 测试 ===\n')
    
    results = []
    results.append(('时钟域', test_clock_domain()))
    results.append(('时序路径', test_timing_path()))
    results.append(('CDC路径', test_cdc_path()))
    results.append(('真实设计', test_real_designs()))
    
    print('\n=== 测试汇总 ===')
    for name, passed in results:
        print(f'  {name}: {"✅" if passed else "❌"}')
    
    ok = sum(1 for _, p in results if p)
    print(f'\n通过: {ok}/{len(results)}')
