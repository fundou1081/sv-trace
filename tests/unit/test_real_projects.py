"""
真实项目测试 - tiny-gpu 和 basic_verilog

用于验证 sv-trace 在实际项目上的表现
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parse import SVParser
from query.hierarchy import HierarchicalResolver


# ========== Tiny-GPU 测试 ==========

TINY_GPU_FILES = [
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
    """测试 tiny-gpu 项目"""
    print("=" * 50)
    print("Tiny-GPU 项目测试")
    print("=" * 50)
    
    parser = SVParser()
    success = 0
    failed = 0
    
    for f in TINY_GPU_FILES:
        try:
            parser.parse_file(f)
            success += 1
        except Exception as e:
            failed += 1
            print(f"  ✗ {os.path.basename(f)}: {e}")
    
    print(f"\n解析结果: {success}/{success+failed} 成功")
    
    resolver = HierarchicalResolver(parser)
    modules = resolver._get_all_modules()
    instances = resolver.get_all_instances()
    
    print(f"模块数: {len(modules)}")
    print(f"实例数: {len(instances)}")
    
    # 测试层级追踪
    print("\n层级追踪测试:")
    test_paths = [
        "gpu.fetcher_instance.pc_reg",    # gpu -> core -> fetcher -> pc
        "core.alu_result",                  # core 模块内的信号
    ]
    
    for path in test_paths:
        result = resolver.resolve_signal(path)
        if result:
            print(f"  ✓ {path} -> {result.get('module', 'N/A')}")
        else:
            print(f"  ✗ {path} -> Not found")
    
    return success > 0 and failed == 0


# ========== Basic Verilog 测试 ==========

def find_sv_files(base_dir, limit=20):
    """查找 SV 文件"""
    files = []
    for root, dirs, filenames in os.walk(base_dir):
        for f in filenames:
            if f.endswith('.sv'):
                files.append(os.path.join(root, f))
                if len(files) >= limit:
                    return files
    return files


def test_basic_verilog():
    """测试 basic_verilog 项目"""
    print("\n" + "=" * 50)
    print("Basic Verilog 项目测试")
    print("=" * 50)
    
    base_dir = "/Users/fundou/my_dv_proj/basic_verilog"
    sv_files = find_sv_files(base_dir, limit=30)
    
    print(f"找到 {len(sv_files)} 个 .sv 文件")
    
    parser = SVParser()
    success = 0
    failed = 0
    
    for f in sv_files[:20]:  # 测试前 20 个
        try:
            parser.parse_file(f)
            success += 1
        except Exception as e:
            failed += 1
    
    print(f"解析结果: {success}/{success+failed} 成功")
    
    resolver = HierarchicalResolver(parser)
    modules = resolver._get_all_modules()
    instances = resolver.get_all_instances()
    
    print(f"模块数: {len(modules)}")
    print(f"实例数: {len(instances)}")
    
    return success > 0


# ========== 主测试 ==========

def main():
    results = {}
    
    results['tiny-gpu'] = test_tiny_gpu()
    results['basic_verilog'] = test_basic_verilog()
    
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(results.values())
    print(f"\n总体: {'✓ ALL PASS' if all_passed else '✗ SOME FAILED'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())


def test_hierarchy_detail():
    """详细层级追踪测试"""
    print("\n" + "=" * 50)
    print("详细层级追踪测试")
    print("=" * 50)
    
    parser = SVParser()
    for f in TINY_GPU_FILES:
        parser.parse_file(f)
    
    resolver = HierarchicalResolver(parser)
    
    # 列出所有实例
    print("\n所有实例:")
    instances = resolver.get_all_instances()
    for inst in instances:
        print(f"  {inst['parent_module']}.{inst['instance_name']} -> {inst['module_type']}")
        for p in inst.get('ports', []):
            print(f"    {p['port']} ({p['direction']}) -> {p['connected_to']}")
    
    # 测试已知路径
    print("\n已知路径测试:")
    
    # gpu 模块中的 dcr
    result = resolver.resolve_signal("gpu.dcr_instance")
    print(f"  gpu.dcr_instance: {result}")
    
    # core 模块中的 fetcher
    result = resolver.resolve_signal("core.fetcher_instance")
    print(f"  core.fetcher_instance: {result}")


if __name__ == "__main__":
    test_hierarchy_detail()
