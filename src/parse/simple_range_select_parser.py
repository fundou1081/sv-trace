"""
Simple Range Select Parser - 使用正确的 AST 遍历

提取简单范围选择：
- SimpleRangeSelect

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class SimpleRangeSelect:
    left: str = ""
    right: str = ""


class SimpleRangeSelectExtractor:
    def __init__(self):
        self.selects: List[SimpleRangeSelect] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'SimpleRangeSelect':
                srs = SimpleRangeSelect()
                if hasattr(node, 'left') and node.left:
                    srs.left = str(node.left)[:20]
                if hasattr(node, 'right') and node.right:
                    srs.right = str(node.right)[:20]
                self.selects.append(srs)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'left': s.left[:15], 'right': s.right[:15]} for s in self.selects[:20]]


def extract_simple_range_selects(code: str) -> List[Dict]:
    return SimpleRangeSelectExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [7:0] arr [0:15];
'''
    result = extract_simple_range_selects(test_code)
    print(f"Simple range selects: {len(result)}")
