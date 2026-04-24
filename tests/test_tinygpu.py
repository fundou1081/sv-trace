"""测试 tiny-gpu 项目"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parse import SVParser
from query.hierarchy import HierarchicalResolver

# 解析 tiny-gpu 所有 .sv 文件
sv_files = [
    "/Users/fundou/my_dv_proj/tiny-gpu/src/alu.sv",
    "/Users/fundou/my_dv_proj/tiny-gpu/src/core.sv",
    "/Users/fundou/my_dv_proj/tiny-gpu/src/gpu.sv",
    "/Users/fundou/my_dv_proj/tiny-gpu/src/controller.sv",
    "/Users/fundou/my_dv_proj/tiny-gpu/src/decoder.sv",
    "/Users/fundou/my_dv_proj/tiny-gpu/src/dispatch.sv",
    "/Users/fundou/my_dv_proj/tiny-gpu/src/fetcher.sv",
    "/Users/fundou/my_dv_proj/tiny-gpu/src/lsu.sv",
    "/Users/fundou/my_dv_proj/tiny-gpu/src/pc.sv",
    "/Users/fundou/my_dv_proj/tiny-gpu/src/registers.sv",
    "/Users/fundou/my_dv_proj/tiny-gpu/src/scheduler.sv",
    "/Users/fundou/my_dv_proj/tiny-gpu/src/dcr.sv",
]

def test_tiny_gpu():
    print("=== Tiny-GPU Test ===\n")
    
    parser = SVParser()
    
    # 解析所有文件
    for f in sv_files:
        try:
            parser.parse_file(f)
            print(f"✓ Parsed: {os.path.basename(f)}")
        except Exception as e:
            print(f"✗ Failed: {os.path.basename(f)} - {e}")
    
    print(f"\nTotal files parsed: {len(parser.trees)}")
    
    # 测试层级解析
    resolver = HierarchicalResolver(parser)
    
    # 获取所有模块
    modules = resolver._get_all_modules()
    print(f"\nModules found: {len(modules)}")
    for m in modules[:5]:
        print(f"  - {m.header.name.value}")
    
    # 获取所有实例
    instances = resolver.get_all_instances()
    print(f"\nInstances found: {len(instances)}")
    for inst in instances[:5]:
        print(f"  - {inst['instance_name']} ({inst['module_type']}) in {inst['parent_module']}")
        for p in inst.get('ports', [])[:3]:
            print(f"      {p['port']}: {p['direction']} -> {p['connected_to']}")

test_tiny_gpu()
