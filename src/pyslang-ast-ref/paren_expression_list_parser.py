"""
Paren Expression List Parser - 使用正确的 AST 遍历

提取括号表达式列表：
- ParenExpressionList

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ParenExpressionList:
    expressions: List[str] = None
    
    def __post_init__(self):
        if self.expressions is None:
            self.expressions = []


class ParenExpressionListExtractor:
    def __init__(self):
        self.lists: List[ParenExpressionList] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ParenExpressionList':
                pel = ParenExpressionList()
                
                exprs = []
                def get_exprs(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Expression' in kn:
                        exprs.append(str(n)[:30])
                    return pyslang.VisitAction.Advance
                node.visit(get_exprs)
                pel.expressions = exprs[:20]
                
                self.lists.append(pel)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'count': len(l.expressions)} for l in self.lists[:20]]


def extract_paren_lists(code: str) -> List[Dict]:
    return ParenExpressionListExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
(a + b, c + d)
'''
    result = extract_paren_lists(test_code)
    print(f"Paren expression lists: {len(result)}")
