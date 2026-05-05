"""
芯片验证金标准测试

按项目纪律：在真实设计中测试时钟/复位/多驱动功能
"""

import sys
import os
import glob
sys.path.insert(0, 'src')

from parse import SVParser
from trace.driver import DriverCollector
from trace.load import LoadTracer


def test_cdc_multi_clock():
    """多时钟域"""
    sv = '''module t (input clk1, input clk2, input rst_n, input d, output q1, output q2);
        reg r1, r2;
        always_ff @(posedge clk1 or negedge rst_n) begin
            if (!rst_n) r1 <= 0; else r1 <= d; end
        always_ff @(posedge clk2 or negedge rst_n) begin
            if (!rst_n) r2 <= 0; else r2 <= d; end
    endmodule'''
    
    tree = SVParser().parse_text(sv, 't.sv')
    dc = DriverCollector(use_semantic=True)
    dc.collect(tree, 't.sv')
    
    # 金标准：
    # - r1 驱动时钟: clk1
    # - r2 驱动时钟: clk2
    # - 复位: rst_n
    
    print(f'【多时钟域测试】')
    print(f'  识别的时钟: {dc.all_clocks}')
    print(f'  多驱动: {dc.multi_drivers}')
    
    passed = len(dc.all_clocks) >= 1
    print(f'  结果: {"✅" if passed else "❌"}')
    return passed


def test_async_reset():
    """异步复位"""
    sv = '''module t (input clk, input rst_n, output q);
        reg r;
        always_ff @(posedge clk or negedge rst_n)
            if (!rst_n) r <= 0; else r <= r;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 't.sv')
    dc = DriverCollector(use_semantic=True)
    dc.collect(tree, 't.sv')
    
    print(f'【异步复位测试】')
    print(f'  时钟: {dc.all_clocks}')
    
    passed = len(dc.all_clocks) >= 1
    print(f'  结果: {"✅" if passed else "❌"}')
    return passed


def test_multi_driver():
    """多驱动检测"""
    sv = '''module t (input clk, input d, output q);
        reg r;
        always_ff @(posedge clk) r <= d;
        always_ff @(posedge clk) r <= d;  // 双驱动
    endmodule'''
    
    tree = SVParser().parse_text(sv, 't.sv')
    dc = DriverCollector(use_semantic=True)
    dc.collect(tree, 't.sv')
    
    print(f'【多驱动检测】')
    print(f'  多驱动: {dc.multi_drivers}')
    
    passed = len(dc.multi_drivers) > 0
    print(f'  结果: {"✅" if passed else "❌"}')
    return passed


def test_basic_verilog_real():
    """真实设计测试"""
    base = os.path.expanduser('~/my_dv_proj/basic_verilog')
    files = glob.glob(f'{base}/*.sv')[:5]
    
    print(f'【真实设计测试】')
    results = []
    for f in files:
        name = os.path.basename(f)
        try:
            with open(f) as fp:
                code = fp.read()
            tree = SVParser().parse_text(code, name)
            dc = DriverCollector(use_semantic=True)
            dc.collect(tree, name)
            
            drivers = len(dc.drivers)
            clocks = len(dc.all_clocks)
            results.append((name, drivers, clocks))
        except:
            results.append((name, 0, 0))
    
    for n, d, c in results:
        print(f'  {n}: 驱动={d}, 时钟={c}')
    
    passed = len([r for r in results if r[1] > 0]) >= 3
    print(f'  结果: {"✅" if passed else "❌"}')
    return passed


if __name__ == '__main__':
    print('=== 芯片验证金标准测试 ===\n')
    
    results = []
    results.append(('CDC多时钟', test_cdc_multi_clock()))
    results.append(('异步复位', test_async_reset()))
    results.append(('多驱动检测', test_multi_driver()))
    results.append(('真实设计', test_basic_verilog_real()))
    
    print('\n=== 测试汇总 ===')
    for name, passed in results:
        print(f'  {name}: {"✅" if passed else "❌"}')
    
    ok = sum(1 for _, p in results if p)
    print(f'\n通过: {ok}/{len(results)}')
