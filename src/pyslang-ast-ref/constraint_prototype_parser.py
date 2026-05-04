"""
Constraint Prototype Parser - 使用正确的 AST 遍历

提取约束原型：
- ConstraintPrototype

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ConstraintPrototype:
    name: str = ""
    soft: bool = False


class ConstraintPrototypeExtractor:
    def __init__(self):
        self.prototypes: List[ConstraintPrototype] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ConstraintPrototype':
                cp = ConstraintPrototype()
                if hasattr(node, 'name') and node.name:
                    cp.name = str(node.name)
                if hasattr(node, 'soft') and node.soft:
                    cp.soft = True
                self.prototypes.append(cp)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': p.name, 'soft': p.soft} for p in self.prototypes]


def extract_constraint_prototypes(code: str) -> List[Dict]:
    return ConstraintPrototypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
virtual function void pre_randomize();
'''
    result = extract_constraint_prototypes(test_code)
    print(f"Constraint prototypes: {len(result)}")
