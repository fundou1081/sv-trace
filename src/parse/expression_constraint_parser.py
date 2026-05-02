"""
Expression Constraint Parser - 使用正确的 AST 遍历

提取表达式约束：
- ExpressionConstraint

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ExpressionConstraint:
    expression: str = ""
    soft: bool = False


class ExpressionConstraintExtractor:
    def __init__(self):
        self.constraints: List[ExpressionConstraint] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ExpressionConstraint':
                ec = ExpressionConstraint()
                if hasattr(node, 'expression') and node.expression:
                    ec.expression = str(node.expression)[:50]
                if hasattr(node, 'soft') and node.soft:
                    ec.soft = True
                self.constraints.append(ec)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'expr': c.expression[:40], 'soft': c.soft} for c in self.constraints]


def extract_expression_constraints(code: str) -> List[Dict]:
    return ExpressionConstraintExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
constraint c1 { soft x == 5; }
'''
    result = extract_expression_constraints(test_code)
    print(f"Expression constraints: {len(result)}")
