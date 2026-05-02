"""
New Keyword V2 Parser - 使用正确的 AST 遍历

提取 new/super/this 关键字：
- NewKeyword
- SuperKeyword
- ThisKeyword

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class NewKeyword:
    keyword: str = ""


class NewKeywordExtractor:
    def __init__(self):
        self.keywords: List[NewKeyword] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['NewKeyword', 'SuperKeyword', 'ThisKeyword', 'NullKeyword']:
                nk = NewKeyword()
                nk.keyword = kind_name.replace('Keyword', '').lower()
                self.keywords.append(nk)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': k.keyword} for k in self.keywords[:100]]


def extract_new_keywords(code: str) -> List[Dict]:
    return NewKeywordExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
class my_class;
    function new();
endclass
'''
    result = extract_new_keywords(test_code)
    print(f"New keywords: {len(result)}")
