"""
Logical Expression Parser - 使用正确的 AST 遍历

提取逻辑表达式：
- LogicalAndExpression
- LogicalOrExpression
- LogicalImplicationExpression
- DoubleAnd
- DoubleOr

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
class LogicalExpr:
    operator: str = ""
    left: str = ""
    right: str = ""


class LogicalExpressionExtractor:
    def __init__(self):
        self.expressions: List[LogicalExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['LogicalAndExpression', 'LogicalOrExpression', 'LogicalImplicationExpression',
                           'DoubleAnd', 'DoubleOr', 'ImplicationExpression', 'BiImplicationExpression']:
                le = LogicalExpr()
                le.operator = '&&' if 'And' in kind_name else '||'
                
                if hasattr(node, 'left') and node.left:
                    le.left = str(node.left)[:30]
                if hasattr(node, 'right') and node.right:
                    le.right = str(node.right)[:30]
                
                self.expressions.append(le)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'op': e.operator, 'left': e.left[:20], 'right': e.right[:20]} for e in self.expressions[:20]]


def extract_logical_expressions(code: str) -> List[Dict]:
    return LogicalExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic a, b, c;
if (a && b) c = 1;
if (a || b) c = 0;
'''
    result = extract_logical_expressions(test_code)
    print(f"Logical expressions: {len(result)}")
