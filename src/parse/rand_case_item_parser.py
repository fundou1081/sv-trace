"""
Rand Case Item Parser - 使用正确的 AST 遍历

提取 rand case 项：
- RandCaseItem

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class RandCaseItem:
    weight: str = ""
    item: str = ""


class RandCaseItemExtractor:
    def __init__(self):
        self.items: List[RandCaseItem] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'RandCaseItem':
                rci = RandCaseItem()
                
                if hasattr(node, 'weight') and node.weight:
                    rci.weight = str(node.weight)[:20]
                
                if hasattr(node, 'item') and node.item:
                    rci.item = str(node.item)[:30]
                
                self.items.append(rci)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'weight': i.weight[:15], 'item': i.item[:25]} for i in self.items]


def extract_rand_case_items(code: str) -> List[Dict]:
    return RandCaseItemExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
randcase
    1: a = 1;
    2: a = 2;
endcase
'''
    result = extract_rand_case_items(test_code)
    print(f"Rand case items: {len(result)}")
