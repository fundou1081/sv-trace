"""
Typedef Keyword Parser - 使用正确的 AST 遍历

提取 typedef/enum/struct 关键字：
- TypedefKeyword
- EnumKeyword
- StructKeyword
- UnionKeyword

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class TypedefKeyword:
    keyword: str = ""


class TypedefKeywordExtractor:
    def __init__(self):
        self.keywords: List[TypedefKeyword] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['TypedefKeyword', 'EnumKeyword', 'StructKeyword', 'UnionKeyword',
                           'PackedKeyword', 'VirtualKeyword', 'PureKeyword', 'ExternKeyword',
                           'StaticKeyword', 'AutomaticKeyword']:
                tk = TypedefKeyword()
                tk.keyword = kind_name.replace('Keyword', '').lower()
                self.keywords.append(tk)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': k.keyword} for k in self.keywords[:50]]


def extract_typedef_keywords(code: str) -> List[Dict]:
    return TypedefKeywordExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
typedef enum { RED, GREEN, BLUE } color_e;
'''
    result = extract_typedef_keywords(test_code)
    print(f"Typedef keywords: {len(result)}")
