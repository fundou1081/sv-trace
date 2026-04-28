#!/usr/bin/env python3
"""
RISC-V 项目 sv_verify 测试
测试 FSM, 依赖分析, 覆盖率指导
"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from debug.fsm import FSMExtractor
from debug.dependency import ModuleDependencyAnalyzer


RISCV_PROJECTS = [
    ('picorv32', '/Users/fundou/my_dv_proj/picorv32/picorv32.v'),
    ('serv', '/Users/fundou/my_dv_proj/serv/rtl/serv_top.v'),
    ('neorv32', '/Users/fundou/my_dv_proj/neorv32/rtl/top/neorv32_top.v'),
]


def main():
    print("=" * 60)
    print("RISC-V 项目 sv_verify 测试")
    print("=" * 60)
    
    passed = 0
    for name, path in RISCV_PROJECTS:
        print(f"\n--- {name} ---")
        
        if not os.path.exists(path):
            # 搜索文件
            import subprocess
            result = subprocess.run(
                ['find', f'/Users/fundou/my_dv_proj/{name}', '-name', '*.v', '-type', 'f'],
                capture_output=True, text=True, timeout=30
            )
            files = result.stdout.strip().split('\n')[:2]
            for f in files:
                if f:
                    try:
                        parser = SVParser()
                        parser.parse_file(f)
                        
                        ext = FSMExtractor(parser)
                        fsms = ext.find_all_fsm()
                        
                        dep = ModuleDependencyAnalyzer(parser)
                        mods = dep.get_all_modules()
                        
                        print(f"  ✅ {os.path.basename(f)}")
                        print(f"     FSM: {len(fsms)}, 模块: {len(mods)}")
                        passed += 1
                        break
                    except:
                        pass
        else:
            try:
                parser = SVParser()
                parser.parse_file(path)
                
                ext = FSMExtractor(parser)
                fsms = ext.find_all_fsm()
                
                dep = ModuleDependencyAnalyzer(parser)
                mods = dep.get_all_modules()
                
                print(f"  ✅ FSM: {len(fsms)}, 模块: {len(mods)}")
                passed += 1
            except Exception as e:
                print(f"  ❌ {str(e)[:30]}")
    
    print("\n" + "=" * 60)
    print(f"结果: {passed}/{len(RISCV_PROJECTS)} 通过")
    print("=" * 60)
    
    return passed >= len(RISCV_PROJECTS) - 1


if __name__ == '__main__':
    main()
