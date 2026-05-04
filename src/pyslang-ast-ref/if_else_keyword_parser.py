"""
If Else Keyword Parser - 使用正确的 AST 遍历

提取 if/else/extends 关键字：
- IfKeyword
- ElseKeyword
- ExtendsKeyword

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class IfElseKeyword:
    keyword: str = ""


class IfElseKeywordExtractor:
    def __init__(self):
        self.keywords: List[IfElseKeyword] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['IfKeyword', 'ElseKeyword', 'ExtendsKeyword', 'ImplementsKeyword']:
                iek = IfElseKeyword()
                iek.keyword = kind_name.replace('Keyword', '').lower()
                self.keywords.append(iek)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': k.keyword} for k in self.keywords[:50]]


def extract_if_else_keywords(code: str) -> List[Dict]:
    return IfElseKeywordExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
if (a) begin end
else begin end
'''
    result = extract_if_else_keywords(test_code)
    print(f"If/Else keywords: {len(result)}")
