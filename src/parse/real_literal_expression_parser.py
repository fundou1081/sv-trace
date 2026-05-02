"""
Real Literal Expression Parser - 使用正确的 AST 遍历

提取实数字面量表达式：
- RealLiteralExpression

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
class RealLiteralExpr:
    value: str = ""


class RealLiteralExpressionExtractor:
    def __init__(self):
        self.expressions: List[RealLiteralExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'RealLiteralExpression':
                rle = RealLiteralExpr()
                if hasattr(node, 'literal') and node.literal:
                    rle.value = str(node.literal)
                elif hasattr(node, 'value') and node.value:
                    rle.value = str(node.value)
                self.expressions.append(rle)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'value': e.value[:30]} for e in self.expressions]


def extract_real_literal_expressions(code: str) -> List[Dict]:
    return RealLiteralExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
real pi = 3.14159;
real e = 2.71828;
'''
    result = extract_real_literal_expressions(test_code)
    print(f"Real literal expressions: {len(result)}")
