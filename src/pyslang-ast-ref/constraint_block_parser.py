"""
Constraint Block Parser - 使用正确的 AST 遍历

提取约束块：
- ConstraintBlock

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ConstraintBlock:
    name: str = ""
    num_constraints: int = 0


class ConstraintBlockExtractor:
    def __init__(self):
        self.blocks: List[ConstraintBlock] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ConstraintBlock':
                cb = ConstraintBlock()
                if hasattr(node, 'name') and node.name:
                    cb.name = str(node.name)
                
                count = 0
                def count_items(n, c=[0]):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Constraint' in kn:
                        c[0] += 1
                    return pyslang.VisitAction.Advance
                node.visit(count_items)
                cb.num_constraints = count
                
                self.blocks.append(cb)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': b.name, 'count': b.num_constraints} for b in self.blocks]


def extract_constraint_blocks(code: str) -> List[Dict]:
    return ConstraintBlockExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
constraint c1 { x inside {[0:10]}; }
'''
    result = extract_constraint_blocks(test_code)
    print(f"Constraint blocks: {len(result)}")
