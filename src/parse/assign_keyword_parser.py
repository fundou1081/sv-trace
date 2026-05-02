"""
Assign Keyword Parser - 使用正确的 AST 遍历

提取 assign 关键字：
- AssignKeyword
- AliasKeyword

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class AssignKeyword:
    keyword: str = ""


class AssignKeywordExtractor:
    def __init__(self):
        self.keywords: List[AssignKeyword] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['AssignKeyword', 'AliasKeyword', 'DeassignKeyword',
                           'ForceKeyword', 'ReleaseKeyword', 'DisableKeyword']:
                ak = AssignKeyword()
                ak.keyword = kind_name.replace('Keyword', '').lower()
                self.keywords.append(ak)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': k.keyword} for k in self.keywords[:50]]


def extract_assign_keywords(code: str) -> List[Dict]:
    return AssignKeywordExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
assign sig = value;
'''
    result = extract_assign_keywords(test_code)
    print(f"Assign keywords: {len(result)}")
