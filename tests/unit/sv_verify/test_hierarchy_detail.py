import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

"""详细测试实例路径解析"""
import sys, os
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from query.hierarchy import HierarchicalResolver

files = [
    '/Users/fundou/my_dv_proj/tiny-gpu/src/gpu.sv',
    '/Users/fundou/my_dv_proj/tiny-gpu/src/core.sv',
    '/Users/fundou/my_dv_proj/tiny-gpu/src/alu.sv',
]

parser = SVParser()
for f in files:
    parser.parse_file(f)

resolver = HierarchicalResolver(parser)

# 测试 resolve_signal - 用于信号
print("resolve_signal (信号):")
result = resolver.resolve_signal("pc_reg")
print(f"  pc_reg: {result}")

# 测试 get_instance_info - 用于实例
print("\nget_instance_info (实例):")
result = resolver.get_instance_info("gpu.dcr_instance")
print(f"  gpu.dcr_instance: {result}")

result = resolver.get_instance_info("core.fetcher_instance")
print(f"  core.fetcher_instance: {result}")
