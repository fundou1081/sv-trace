"""
Separated List Parser - 使用正确的 AST 遍历

提取分隔列表：
- SeparatedList

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class SeparatedList:
    items: List[str] = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []


class SeparatedListExtractor:
    def __init__(self):
        self.lists: List[SeparatedList] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'SeparatedList':
                sl = SeparatedList()
                
                items = []
                def get_items(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Identifier' in kn or 'Name' in kn or 'Expression' in kn:
                        if kn not in ['IdentifierName', 'Identifier']:
                            items.append(str(n)[:30])
                    return pyslang.VisitAction.Advance
                node.visit(get_items)
                sl.items = items[:30]
                
                self.lists.append(sl)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'count': len(l.items)} for l in self.lists[:20]]


def extract_separated_lists(code: str) -> List[Dict]:
    return SeparatedListExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
a, b, c
'''
    result = extract_separated_lists(test_code)
    print(f"Separated lists: {len(result)}")
