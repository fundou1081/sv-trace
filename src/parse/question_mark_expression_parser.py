"""
Question Mark Expression Parser - 使用正确的 AST 遍历

提取三元条件表达式：
- Question (the ? operator)

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ConditionalExpression:
    condition: str = ""
    then_expr: str = ""
    else_expr: str = ""


class ConditionalExpressionExtractor:
    def __init__(self):
        self.expressions: List[ConditionalExpression] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ConditionalExpression', 'Question']:
                ce = ConditionalExpression()
                
                if hasattr(node, 'condition') and node.condition:
                    ce.condition = str(node.condition)[:30]
                
                if hasattr(node, 'then') and node.then:
                    ce.then_expr = str(node.then)[:25]
                
                if hasattr(node, 'else') and node.else_clause:
                    ce.else_expr = str(node.else_clause)[:25]
                
                self.expressions.append(ce)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'cond': e.condition[:25], 'then': e.then_expr[:20], 'else': e.else_expr[:20]} for e in self.expressions[:20]]


def extract_conditional_expressions(code: str) -> List[Dict]:
    return ConditionalExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic a = (b > 5) ? c : d;
'''
    result = extract_conditional_expressions(test_code)
    print(f"Conditional expressions: {len(result)}")
