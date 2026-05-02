"""
Postincrement Expression Parser - 使用正确的 AST 遍历

提取后递增/后递减表达式：
- PostincrementExpression
- PostdecrementExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class PostIncrementExpr:
    operator: str = ""
    operand: str = ""


class PostIncrementExpressionExtractor:
    def __init__(self):
        self.expressions: List[PostIncrementExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['PostincrementExpression', 'PostdecrementExpression']:
                pie = PostIncrementExpr()
                pie.operator = '++' if 'increment' in kind_name.lower() else '--'
                
                if hasattr(node, 'operand') and node.operand:
                    pie.operand = str(node.operand)[:30]
                elif hasattr(node, 'expression') and node.expression:
                    pie.operand = str(node.expression)[:30]
                
                self.expressions.append(pie)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'op': e.operator, 'operand': e.operand[:30]} for e in self.expressions[:20]]


def extract_post_increment(code: str) -> List[Dict]:
    return PostIncrementExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
int i = 0;
i++;
'''
    result = extract_post_increment(test_code)
    print(f"Post increment: {len(result)}")
