"""
Expression Parser - 使用正确的 AST 遍历

提取表达式：
- AssignmentExpression
- ConditionalExpression
- EqualityExpression
- BinaryExpression
- UnaryExpression
- etc.

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
class Expression:
    expr_type: str = ""
    operator: str = ""
    left: str = ""
    right: str = ""


class ExpressionExtractor:
    def __init__(self):
        self.expressions: List[Expression] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # AssignmentExpression
            if kind_name == 'AssignmentExpression':
                e = Expression()
                e.expr_type = 'assignment'
                if hasattr(node, 'left') and node.left:
                    e.left = str(node.left)
                if hasattr(node, 'right') and node.right:
                    e.right = str(node.right)
                if hasattr(node, 'operator') and node.operator:
                    e.operator = str(node.operator)
                self.expressions.append(e)
            
            # ConditionalExpression
            elif kind_name == 'ConditionalExpression':
                e = Expression()
                e.expr_type = 'conditional'
                if hasattr(node, 'condition') and node.condition:
                    e.left = str(node.condition)
                self.expressions.append(e)
            
            # EqualityExpression
            elif kind_name == 'EqualityExpression':
                e = Expression()
                e.expr_type = 'equality'
                if hasattr(node, 'left') and node.left:
                    e.left = str(node.left)
                if hasattr(node, 'right') and node.right:
                    e.right = str(node.right)
                if hasattr(node, 'operator') and node.operator:
                    e.operator = str(node.operator)
                self.expressions.append(e)
            
            # BinaryExpression (arithmetic, logic)
            elif kind_name == 'BinaryExpression':
                e = Expression()
                e.expr_type = 'binary'
                if hasattr(node, 'left') and node.left:
                    e.left = str(node.left)[:30]
                if hasattr(node, 'right') and node.right:
                    e.right = str(node.right)[:30]
                if hasattr(node, 'operator') and node.operator:
                    e.operator = str(node.operator)
                self.expressions.append(e)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'type': e.expr_type, 'op': e.operator, 'left': e.left[:30], 'right': e.right[:30]}
            for e in self.expressions[:20]
        ]


def extract_expressions(code: str) -> List[Dict]:
    return ExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    logic [7:0] a, b, c;
    always begin
        a = b + c;
        if (a == b) c = 0;
    end
endmodule
'''
    result = extract_expressions(test_code)
    print(f"Expressions: {len(result)}")
