"""
Uniqueness Constraint Parser - 使用正确的 AST 遍历

提取唯一性约束：
- UniquenessConstraint

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class UniquenessConstraint:
    variables: List[str] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = []


class UniquenessConstraintExtractor:
    def __init__(self):
        self.constraints: List[UniquenessConstraint] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'UniquenessConstraint':
                uc = UniquenessConstraint()
                
                vars = []
                def get_vars(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Identifier' in kn:
                        vars.append(str(n))
                    return pyslang.VisitAction.Advance
                node.visit(get_vars)
                uc.variables = vars[:10]
                
                self.constraints.append(uc)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'vars': c.variables[:5]} for c in self.constraints]


def extract_uniqueness_constraints(code: str) -> List[Dict]:
    return UniquenessConstraintExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
constraint c { unique {a, b, c}; }
'''
    result = extract_uniqueness_constraints(test_code)
    print(f"Uniqueness constraints: {len(result)}")
