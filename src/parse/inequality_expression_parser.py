"""
Inequality Expression Parser - 使用正确的 AST 遍历

提取不等式表达式：
- InequalityExpression
- LessThanExpression
- GreaterThanExpression

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
class ComparisonExpr:
    operator: str = ""
    left: str = ""
    right: str = ""


class InequalityExpressionExtractor:
    def __init__(self):
        self.expressions: List[ComparisonExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['InequalityExpression', 'LessThanExpression', 
                           'GreaterThanExpression', 'LessThanEqualExpression',
                           'GreaterThanEqualExpression']:
                ce = ComparisonExpr()
                ce.operator = kind_name.replace('Expression', '')
                
                if hasattr(node, 'left') and node.left:
                    ce.left = str(node.left)[:30]
                if hasattr(node, 'right') and node.right:
                    ce.right = str(node.right)[:30]
                
                self.expressions.append(ce)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'op': e.operator, 'left': e.left[:20], 'right': e.right[:20]} for e in self.expressions[:20]]


def extract_comparisons(code: str) -> List[Dict]:
    return InequalityExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
if (a < b) begin end
if (a > b) begin end
'''
    result = extract_comparisons(test_code)
    print(f"Comparisons: {len(result)}")
