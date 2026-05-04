"""
Parenthesized Expression Parser - 使用正确的 AST 遍历

提取括号表达式：
- ParenthesizedExpression
- ParenthesizedEventExpression

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
class ParenthesizedExpr:
    inner_expression: str = ""
    is_event: bool = False


class ParenthesizedExpressionExtractor:
    def __init__(self):
        self.expressions: List[ParenthesizedExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ParenthesizedExpression':
                pe = ParenthesizedExpr()
                if hasattr(node, 'expression') and node.expression:
                    pe.inner_expression = str(node.expression)
                self.expressions.append(pe)
            
            elif kind_name == 'ParenthesizedEventExpression':
                pe = ParenthesizedExpr()
                pe.is_event = True
                if hasattr(node, 'event') and node.event:
                    pe.inner_expression = str(node.event)
                self.expressions.append(pe)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'expr': e.inner_expression[:30], 'is_event': e.is_event}
            for e in self.expressions[:20]
        ]


def extract_parenthesized(code: str) -> List[Dict]:
    return ParenthesizedExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
always @(a + b) begin
end
'''
    result = extract_parenthesized(test_code)
    print(f"Parenthesized expressions: {len(result)}")
