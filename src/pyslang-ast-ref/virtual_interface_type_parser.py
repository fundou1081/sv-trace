"""
Virtual Interface Type Parser - 使用正确的 AST 遍历

提取虚拟接口类型：
- VirtualInterfaceType

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class VirtualInterfaceType:
    interface_name: str = ""


class VirtualInterfaceTypeExtractor:
    def __init__(self):
        self.types: List[VirtualInterfaceType] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'VirtualInterfaceType':
                vit = VirtualInterfaceType()
                if hasattr(node, 'interface') and node.interface:
                    vit.interface_name = str(node.interface)
                elif hasattr(node, 'name') and node.name:
                    vit.interface_name = str(node.name)
                self.types.append(vit)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'interface': t.interface_name} for t in self.types]


def extract_virtual_interface_types(code: str) -> List[Dict]:
    return VirtualInterfaceTypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
virtual interface my_if vif;
'''
    result = extract_virtual_interface_types(test_code)
    print(f"Virtual interface types: {len(result)}")
