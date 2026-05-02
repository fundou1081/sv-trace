"""
Add Expression Parser - 使用正确的 AST 遍历

提取加法类表达式：
- AddExpression
- SubtractExpression
- MultiplyExpression
- DivideExpression

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
class BinaryArithExpr:
    expr_type: str = ""
    operator: str = ""
    left: str = ""
    right: str = ""


class BinaryExpressionExtractor:
    def __init__(self):
        self.expressions: List[BinaryArithExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['AddExpression', 'SubtractExpression', 'MultiplyExpression', 
                            'DivideExpression', 'ModuloExpression', 'PowerExpression']:
                e = BinaryArithExpr()
                e.expr_type = kind_name.replace('Expression', '').lower()
                
                if hasattr(node, 'left') and node.left:
                    e.left = str(node.left)[:30]
                if hasattr(node, 'right') and node.right:
                    e.right = str(node.right)[:30]
                
                self.expressions.append(e)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'type': e.expr_type, 'left': e.left, 'right': e.right}
            for e in self.expressions[:20]
        ]


def extract_arithmetic(code: str) -> List[Dict]:
    return BinaryExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [7:0] result = a + b - c * d / e;
'''
    result = extract_arithmetic(test_code)
    print(f"Arithmetic expressions: {len(result)}")
