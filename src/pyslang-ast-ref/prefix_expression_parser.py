"""
Prefix Expression Parser - 使用正确的 AST 遍历

提取前缀表达式：
- UnaryPreincrementExpression
- PrefixIncrementExpression
- PrefixDecrementExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class PrefixExpression:
    operator: str = ""
    operand: str = ""


class PrefixExpressionExtractor:
    def __init__(self):
        self.expressions: List[PrefixExpression] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['UnaryPreincrementExpression', 'UnaryPredecrementExpression',
                           'PrefixIncrementExpression', 'PrefixDecrementExpression']:
                pe = PrefixExpression()
                
                if 'increment' in kind_name.lower():
                    pe.operator = '++'
                else:
                    pe.operator = '--'
                
                if hasattr(node, 'operand') and node.operand:
                    pe.operand = str(node.operand)[:30]
                
                self.expressions.append(pe)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'op': e.operator, 'operand': e.operand[:30]} for e in self.expressions[:20]]


def extract_prefix_expressions(code: str) -> List[Dict]:
    return PrefixExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
++a;
--b;
'''
    result = extract_prefix_expressions(test_code)
    print(f"Prefix expressions: {len(result)}")
