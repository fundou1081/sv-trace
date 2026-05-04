"""
Struct Type Parser - 使用正确的 AST 遍历

提取结构体类型：
- StructType

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class StructType:
    packed: bool = False
    tagged: bool = False
    member_count: int = 0


class StructTypeExtractor:
    def __init__(self):
        self.types: List[StructType] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'StructType':
                st = StructType()
                if hasattr(node, 'packed') and node.packed:
                    st.packed = True
                if hasattr(node, 'tagged') and node.tagged:
                    st.tagged = True
                
                count = 0
                def count_members(n, c=[0]):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Member' in kn:
                        c[0] += 1
                    return pyslang.VisitAction.Advance
                node.visit(count_members)
                st.member_count = count
                
                self.types.append(st)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'packed': t.packed, 'tagged': t.tagged, 'members': t.member_count} for t in self.types]


def extract_struct_types(code: str) -> List[Dict]:
    return StructTypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
struct packed { logic [7:0] a; logic [7:0] b; } s;
'''
    result = extract_struct_types(test_code)
    print(f"Struct types: {len(result)}")
