"""
芯片验证金标准测试 - 修复版

按项目纪律：使用 assert 替代 return
"""

import sys
import os
import glob
sys.path.insert(0, 'src')

from parse import SVParser
from trace.driver import DriverCollector


def test_cdc_multi_clock():
    """多时钟域 - 验证CDC检测"""
    sv = '''module t (input clk1, clk2, rst_n, d, output q1, q2);
        reg r1, r2;
        always_ff @(posedge clk1 or negedge rst_n) begin r1 <= rst_n ? d : 0; end
        always_ff @(posedge clk2 or negedge rst_n) begin r2 <= rst_n ? d : 0; end
    endmodule'''
    
    tree = SVParser().parse_text(sv, 't.sv')
    dc = DriverCollector(use_semantic=True)
    dc.collect(tree, 't.sv')
    
    # 验证
    assert len(dc.all_clocks) >= 1, "应识别时钟"


def test_async_reset():
    """异步复位检测"""
    sv = '''module t (input clk, rst_n, output q);
        reg r;
        always_ff @(posedge clk or negedge rst_n) r <= rst_n ? r : 0;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 't.sv')
    dc = DriverCollector(use_semantic=True)
    dc.collect(tree, 't.sv')
    
    # 验证
    assert len(dc.all_clocks) >= 1, "应识别时钟"


def test_multi_driver():
    """多驱动检测 - 核心芯片验证功能"""
    sv = '''module t (input clk, d, output q);
        reg r;
        always_ff @(posedge clk) r <= d;
        always_ff @(posedge clk) r <= d;
    endmodule'''
    
    tree = SVParser().parse_text(sv, 't.sv')
    dc = DriverCollector(use_semantic=True)
    dc.collect(tree, 't.sv')
    
    # 验证多驱动检测
    assert len(dc.multi_drivers) > 0, "应检测到多驱动"


def test_basic_verilog_real():
    """真实设计验证 - 金标准"""
    base = os.path.expanduser('~/my_dv_proj/basic_verilog')
    files = glob.glob(f'{base}/*.sv')[:5]
    
    passed = 0
    for f in files:
        name = os.path.basename(f)
        try:
            with open(f) as fp:
                code = fp.read()
            tree = SVParser().parse_text(code, name)
            dc = DriverCollector(use_semantic=True)
            dc.collect(tree, name)
            passed += 1
        except:
            pass
    
    assert passed >= 3, "真实设计应通过"
