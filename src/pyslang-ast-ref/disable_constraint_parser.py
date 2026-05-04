"""
Disable Constraint Parser - 使用正确的 AST 遍历

提取禁用约束：
- DisableConstraint

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class DisableConstraint:
    constraint_name: str = ""


class DisableConstraintExtractor:
    def __init__(self):
        self.constraints: List[DisableConstraint] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'DisableConstraint':
                dc = DisableConstraint()
                if hasattr(node, 'constraint') and node.constraint:
                    dc.constraint_name = str(node.constraint)
                elif hasattr(node, 'name') and node.name:
                    dc.constraint_name = str(node.name)
                self.constraints.append(dc)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'constraint': c.constraint_name[:30]} for c in self.constraints]


def extract_disable_constraints(code: str) -> List[Dict]:
    return DisableConstraintExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
constraint c { disable c1; }
'''
    result = extract_disable_constraints(test_code)
    print(f"Disable constraints: {len(result)}")
