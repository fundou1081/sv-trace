"""
开源设计金标准测试

在 basic_verilog 项目中验证 Driver/Load/Connection 功能
"""

import sys
import os
import glob
sys.path.insert(0, 'src')

from parse import SVParser
from trace.driver import DriverCollector
from trace.load import LoadTracer
from trace.connection import ConnectionTracer


def test_basic_verilog_designs():
    """测试 basic_verilog 项目中的设计"""
    base = os.path.expanduser('~/my_dv_proj/basic_verilog')
    sv_files = glob.glob(f'{base}/*.sv')
    
    results = []
    for path in sorted(sv_files)[:10]:
        name = os.path.basename(path)
        try:
            with open(path) as f:
                sv_code = f.read()
            
            tree = SVParser().parse_text(sv_code, name)
            
            dc = DriverCollector(use_semantic=True)
            dc.collect(tree, name)
            
            lt = LoadTracer(use_semantic=True)
            lt.collect(tree, name)
            
            ct = ConnectionTracer(use_semantic=True)
            ct.collect(tree, name)
            
            results.append({
                'name': name,
                'drivers': len(dc.drivers),
                'loads': len(lt.loads),
                'instances': len(ct.instances),
            })
        except Exception as e:
            results.append({'name': name, 'error': str(e)})
    
    return results


if __name__ == '__main__':
    results = test_basic_verilog_designs()
    
    print('\n=== 金标准测试结果 ===')
    for r in results:
        if 'error' in r:
            print(f"{r['name']}: ERROR")
        else:
            print(f"{r['name']:25s} 驱动={r['drivers']:2d} 负载={r['loads']:2d} 实例={r['instances']:2d}")
    
    passed = len([r for r in results if 'error' not in r])
    print(f'\n通过: {passed}/{len(results)}')
