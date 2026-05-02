"""
Cast Expression Parser - 使用正确的 AST 遍历

提取类型转换表达式：
- CastExpression
- SignedCastExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class CastExpression:
    cast_type: str = ""
    expression: str = ""


class CastExpressionExtractor:
    def __init__(self):
        self.expressions: List[CastExpression] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['CastExpression', 'SignedCastExpression', 'TypeCastExpression']:
                ce = CastExpression()
                if hasattr(node, 'castType') and node.castType:
                    ce.cast_type = str(node.castType)[:20]
                if hasattr(node, 'expression') and node.expression:
                    ce.expression = str(node.expression)[:30]
                self.expressions.append(ce)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': e.cast_type[:20], 'expr': e.expression[:30]} for e in self.expressions[:20]]


def extract_cast_expressions(code: str) -> List[Dict]:
    return CastExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [7:0] a;
a = 8'(b);
'''
    result = extract_cast_expressions(test_code)
    print(f"Cast expressions: {len(result)}")
