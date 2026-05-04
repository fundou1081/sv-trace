"""
Union Type Parser - 使用正确的 AST 遍历

提取 union 类型：
- UnionType

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class UnionType:
    tagged: bool = False
    member_count: int = 0


class UnionTypeExtractor:
    def __init__(self):
        self.types: List[UnionType] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'UnionType':
                ut = UnionType()
                if hasattr(node, 'tagged') and node.tagged:
                    ut.tagged = True
                
                count = 0
                def count_members(n, c=[0]):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Member' in kn:
                        c[0] += 1
                    return pyslang.VisitAction.Advance
                node.visit(count_members)
                ut.member_count = count
                
                self.types.append(ut)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'tagged': t.tagged, 'members': t.member_count} for t in self.types]


def extract_union_types(code: str) -> List[Dict]:
    return UnionTypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
union packed { logic [7:0] a; logic [15:0] b; } u;
'''
    result = extract_union_types(test_code)
    print(f"Union types: {len(result)}")
