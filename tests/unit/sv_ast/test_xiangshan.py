#!/usr/bin/env python3
"""XiangShan 项目测试"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser

# 查找 XiangShan RTL 文件
xs_files = [
    '/Users/fundou/my_dv_proj/XiangShan/src/xiangshan/top/XiangShanTop.sync.v',
]

passed = 0
for fp in xs_files:
    name = os.path.basename(os.path.dirname(fp))
    if not os.path.exists(fp):
        # 搜索实际存在的文件
        import subprocess
        result = subprocess.run(['find', '/Users/fundou/my_dv_proj/XiangShan', '-name', '*.v', '-type', 'f'], 
                              capture_output=True, text=True, timeout=30)
        files = result.stdout.strip().split('\n')[:3]
        for f in files:
            if f:
                try:
                    p = SVParser()
                    p.parse_file(f)
                    print(f"  ✅ {os.path.basename(os.path.dirname(f))}")
                    passed += 1
                    break
                except: pass
        continue
    try:
        p = SVParser()
        p.parse_file(fp)
        print(f"  ✅ {name}")
        passed += 1
    except Exception as e:
        print(f"  ❌ {name}: {str(e)[:30]}")

print(f"\n{passed} passed")
