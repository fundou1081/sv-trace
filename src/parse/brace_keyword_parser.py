"""
Brace Keyword Parser - 使用正确的 AST 遍历

提取大括号关键字：
- OpenBrace
- CloseBrace
- OpenCurly
- CloseCurly

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class BraceKeyword:
    pass


class BraceKeywordExtractor:
    def __init__(self):
        self.count: int = 0
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['OpenBrace', 'CloseBrace', 'OpenCurly', 'CloseCurly']:
                self.count += 1
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'count': self.count}]


def extract_brace_keywords(code: str) -> List[Dict]:
    return BraceKeywordExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
{a, b, c}
'''
    result = extract_brace_keywords(test_code)
    print(f"Brace keywords: {len(result)}")
