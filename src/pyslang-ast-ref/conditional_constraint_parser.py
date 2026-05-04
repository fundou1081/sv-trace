"""
Conditional Constraint Parser - 使用正确的 AST 遍历

提取条件约束：
- ConditionalConstraint

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ConditionalConstraint:
    condition: str = ""
    then_expr: str = ""
    else_expr: str = ""


class ConditionalConstraintExtractor:
    def __init__(self):
        self.constraints: List[ConditionalConstraint] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ConditionalConstraint':
                cc = ConditionalConstraint()
                
                if hasattr(node, 'condition') and node.condition:
                    cc.condition = str(node.condition)[:40]
                
                if hasattr(node, 'then') and node.then:
                    cc.then_expr = str(node.then)[:30]
                
                if hasattr(node, 'else') and node.else_clause:
                    cc.else_expr = str(node.else_clause)[:30]
                
                self.constraints.append(cc)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'cond': c.condition[:40], 'then': c.then_expr[:25], 'else': c.else_expr[:25]} for c in self.constraints]


def extract_conditional_constraints(code: str) -> List[Dict]:
    return ConditionalConstraintExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
constraint c { if (a) x > 5; else x < 3; }
'''
    result = extract_conditional_constraints(test_code)
    print(f"Conditional constraints: {len(result)}")
