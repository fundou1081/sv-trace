"""
Implication Constraint Parser - 使用正确的 AST 遍历

提取蕴含约束：
- ImplicationConstraint
- ElseConstraintClause

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ImplicationConstraint:
    condition: str = ""
    constraint: str = ""


class ImplicationConstraintExtractor:
    def __init__(self):
        self.constraints: List[ImplicationConstraint] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ImplicationConstraint', 'ElseConstraintClause', 'IfConstraint']:
                ic = ImplicationConstraint()
                
                if hasattr(node, 'condition') and node.condition:
                    ic.condition = str(node.condition)[:40]
                
                if hasattr(node, 'constraint') and node.constraint:
                    ic.constraint = str(node.constraint)[:40]
                elif hasattr(node, 'elseClause') and node.elseClause:
                    ic.constraint = str(node.elseClause)[:40]
                
                self.constraints.append(ic)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'cond': c.condition[:30], 'constraint': c.constraint[:30]} for c in self.constraints]


def extract_implication_constraints(code: str) -> List[Dict]:
    return ImplicationConstraintExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
constraint c { if (a) b == 5; }
'''
    result = extract_implication_constraints(test_code)
    print(f"Implication constraints: {len(result)}")
