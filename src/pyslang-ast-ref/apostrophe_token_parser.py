"""
Apostrophe Token Parser - 使用正确的 AST 遍历

提取单引号标记：
- Apostrophe (')
- ApostropheToken

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ApostropheToken:
    pass


class ApostropheTokenExtractor:
    def __init__(self):
        self.count: int = 0
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ["Apostrophe", "ApostropheToken"]:
                self.count += 1
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'count': self.count}]


def extract_apostrophes(code: str) -> List[Dict]:
    return ApostropheTokenExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [7:0] a = 8'(b);
'''
    result = extract_apostrophes(test_code)
    print(f"Apostrophes: {len(result)}")
