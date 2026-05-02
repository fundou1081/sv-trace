"""
Dist Item Parser - 使用正确的 AST 遍历

提取分布项：
- DistItem
- DistWeight
- ExpressionOrDist

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class DistItem:
    value: str = ""
    weight: str = ""


class DistItemExtractor:
    def __init__(self):
        self.items: List[DistItem] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['DistItem', 'DistWeight', 'ExpressionOrDist']:
                di = DistItem()
                
                if hasattr(node, 'value') and node.value:
                    di.value = str(node.value)[:30]
                
                if hasattr(node, 'weight') and node.weight:
                    di.weight = str(node.weight)[:20]
                
                self.items.append(di)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'value': i.value[:25], 'weight': i.weight[:15]} for i in self.items[:20]]


def extract_dist_items(code: str) -> List[Dict]:
    return DistItemExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
randomize with { a dist {0 := 5, 1 := 10}; }
'''
    result = extract_dist_items(test_code)
    print(f"Dist items: {len(result)}")
