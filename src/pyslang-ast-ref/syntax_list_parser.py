"""
Syntax List Parser - 使用正确的 AST 遍历

提取语法列表：
- SyntaxList

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class SyntaxList:
    count: int = 0


class SyntaxListExtractor:
    def __init__(self):
        self.lists: List[SyntaxList] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'SyntaxList':
                sl = SyntaxList()
                if hasattr(node, 'items') and node.items:
                    sl.count = len(list(node.items)) if hasattr(node.items, '__iter__') else 1
                self.lists.append(sl)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'count': l.count} for l in self.lists[:100]]


def extract_syntax_lists(code: str) -> List[Dict]:
    return SyntaxListExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
a, b, c, d
'''
    result = extract_syntax_lists(test_code)
    print(f"Syntax lists: {len(result)}")
