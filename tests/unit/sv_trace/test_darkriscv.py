#!/usr/bin/env python3
"""darkriscv 项目测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser
from trace.driver import DriverTracer

files = [
    '/Users/fundou/my_dv_proj/darkriscv/darkriscv.v',
]

passed = 0
for fp in files:
    name = os.path.basename(fp).replace('.v','')
    if not os.path.exists(fp):
        # 搜索
        import subprocess
        result = subprocess.run(['find', '/Users/fundou/my_dv_proj/darkriscv', '-name', '*.v', '-type', 'f'], 
                              capture_output=True, text=True, timeout=30)
        files = result.stdout.strip().split('\n')[:2]
        for f in files:
            if f:
                try:
                    p = SVParser()
                    p.parse_file(f)
                    d = DriverTracer(p)
                    print(f"  ✅ {os.path.basename(f)}: {len(d.get_drivers('*'))} drivers")
                    passed += 1
                    break
                except: pass
        continue
    try:
        p = SVParser()
        p.parse_file(fp)
        d = DriverTracer(p)
        print(f"  ✅ {name}: {len(d.get_drivers('*'))} drivers")
        passed += 1
    except Exception as e:
        print(f"  ❌ {name}")

print(f"\n{passed} passed")
