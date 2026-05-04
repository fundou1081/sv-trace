"""
Concatenation Expression Parser - 使用正确的 AST 遍历

提取连接表达式：
- ConcatenationExpression
- MultipleConcatenationExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ConcatenationExpression:
    expressions: List[str] = None
    
    def __post_init__(self):
        if self.expressions is None:
            self.expressions = []


class ConcatenationExpressionExtractor:
    def __init__(self):
        self.expressions: List[ConcatenationExpression] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ConcatenationExpression', 'MultipleConcatenationExpression']:
                ce = ConcatenationExpression()
                
                exprs = []
                def get_exprs(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Expression' in kn and kn not in ['ConcatenationExpression', 'MultipleConcatenationExpression']:
                        exprs.append(str(n)[:20])
                    return pyslang.VisitAction.Advance
                node.visit(get_exprs)
                ce.expressions = exprs[:20]
                
                self.expressions.append(ce)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'count': len(e.expressions)} for e in self.expressions[:20]]


def extract_concatenations(code: str) -> List[Dict]:
    return ConcatenationExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [7:0] a = {1, 2, 3, 4};
'''
    result = extract_concatenations(test_code)
    print(f"Concatenations: {len(result)}")
