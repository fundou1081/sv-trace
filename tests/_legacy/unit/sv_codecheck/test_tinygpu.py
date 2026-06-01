#!/usr/bin/env python3
"""tiny-gpu 项目测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser
from trace.driver import DriverTracer

import subprocess
result = subprocess.run(['find', '/Users/fundou/my_dv_proj/tiny-gpu', '-name', '*.sv', '-type', 'f'], 
                      capture_output=True, text=True, timeout=30)
sv_files = result.stdout.strip().split('\n')[:3]

passed = 0
for f in sv_files:
    if f and os.path.exists(f):
        try:
            p = SVParser()
            p.parse_file(f)
            d = DriverTracer(p)
            print(f"  ✅ {os.path.basename(f)}: {len(d.get_drivers('*'))} drivers")
            passed += 1
        except Exception as e:
            print(f"  ❌ {os.path.basename(f)}")

print(f"\n{passed} passed")
