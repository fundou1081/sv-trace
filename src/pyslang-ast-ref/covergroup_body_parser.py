"""
Covergroup Body Parser - 使用正确的 AST 遍历

提取覆盖组体：
- CovergroupBody

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class CovergroupBody:
    members: int = 0


class CovergroupBodyExtractor:
    def __init__(self):
        self.bodies: List[CovergroupBody] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'CovergroupBody':
                cgb = CovergroupBody()
                
                count = 0
                def count_members(n, c=[0]):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Coverpoint' in kn or 'Cross' in kn:
                        c[0] += 1
                    return pyslang.VisitAction.Advance
                node.visit(count_members)
                cgb.members = count
                
                self.bodies.append(cgb)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'members': b.members} for b in self.bodies]


def extract_covergroup_bodies(code: str) -> List[Dict]:
    return CovergroupBodyExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
covergroup cg @(posedge clk);
    coverpoint a;
endgroup
'''
    result = extract_covergroup_bodies(test_code)
    print(f"Covergroup bodies: {len(result)}")
