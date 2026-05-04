"""
Struct/Union Member Parser - 使用正确的 AST 遍历

提取结构体/联合体成员：
- StructUnionMember

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class StructUnionMember:
    names: List[str] = None
    data_type: str = ""
    
    def __post_init__(self):
        if self.names is None:
            self.names = []


class StructUnionMemberExtractor:
    def __init__(self):
        self.members: List[StructUnionMember] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'StructUnionMember':
                sum = StructUnionMember()
                if hasattr(node, 'dataType') and node.dataType:
                    sum.data_type = str(node.dataType)[:30]
                
                names = []
                def get_names(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if kn in ['Identifier', 'VariableDeclarator']:
                        names.append(str(n))
                    return pyslang.VisitAction.Advance
                node.visit(get_names)
                sum.names = names[:10]
                
                self.members.append(sum)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'names': m.names[:5], 'type': m.data_type[:20]} for m in self.members]


def extract_struct_members(code: str) -> List[Dict]:
    return StructUnionMemberExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
struct packed {
    logic [7:0] a, b;
};
'''
    result = extract_struct_members(test_code)
    print(f"Struct members: {len(result)}")
