"""
Empty Member Parser - 使用正确的 AST 遍历

提取空成员：
- EmptyMember
- EmptyStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class EmptyMember:
    member_type: str = ""


class EmptyMemberExtractor:
    def __init__(self):
        self.members: List[EmptyMember] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['EmptyMember', 'EmptyStatement', 'EmptyClassItem']:
                em = EmptyMember()
                em.member_type = kind_name.replace('Member', '').replace('Statement', '').replace('Item', '')
                self.members.append(em)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': m.member_type} for m in self.members]


def extract_empty_members(code: str) -> List[Dict]:
    return EmptyMemberExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
struct packed {
    ;
};
'''
    result = extract_empty_members(test_code)
    print(f"Empty members: {len(result)}")
