"""
Void Type Parser - 使用正确的 AST 遍历

提取 void 类型：
- VoidType

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
class VoidType:
    keyword: str = "void"


class VoidTypeExtractor:
    def __init__(self):
        self.void_types: List[VoidType] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'VoidType':
                v = VoidType()
                if hasattr(node, 'keyword') and node.keyword:
                    v.keyword = str(node.keyword)
                self.void_types.append(v)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': v.keyword} for v in self.void_types]


def extract_void_types(code: str) -> List[Dict]:
    return VoidTypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
function void my_task();
endfunction
'''
    result = extract_void_types(test_code)
    print(f"Void types: {len(result)}")
