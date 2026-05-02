"""
Unary/Bitwise Expression Parser - 使用正确的 AST 遍历

提取一元和位运算表达式：
- UnaryBitwiseNotExpression
- LogicalNotExpression

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
class UnaryExpr:
    operator: str = ""
    operand: str = ""


class UnaryBitwiseExpressionExtractor:
    def __init__(self):
        self.expressions: List[UnaryExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['UnaryBitwiseNotExpression', 'BitwiseNotExpression',
                           'LogicalNotExpression', 'UnaryLogicalNotExpression',
                           'NegationExpression', 'ComplementExpression']:
                ue = UnaryExpr()
                ue.operator = kind_name.replace('Expression', '').replace('Not', '!')
                
                if hasattr(node, 'operand') and node.operand:
                    ue.operand = str(node.operand)[:30]
                elif hasattr(node, 'expression') and node.expression:
                    ue.operand = str(node.expression)[:30]
                
                self.expressions.append(ue)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'op': e.operator, 'operand': e.operand[:30]} for e in self.expressions[:20]]


def extract_unary_expressions(code: str) -> List[Dict]:
    return UnaryBitwiseExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic a, b;
a = ~b;
a = !b;
'''
    result = extract_unary_expressions(test_code)
    print(f"Unary expressions: {len(result)}")
