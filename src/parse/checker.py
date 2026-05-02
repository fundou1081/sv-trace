"""
Checker Parser - 使用正确的 AST 遍历

checker 声明提取

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class CheckerDeclaration:
    name: str = ""
    ports: List[str] = ()


class CheckerExtractor:
    """提取 checker 声明"""
    
    def __init__(self):
        self.checkers: List[CheckerDeclaration] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'CheckerDeclaration':
                checker = CheckerDeclaration()
                if hasattr(node, 'name') and node.name:
                    checker.name = str(node.name)
                self.checkers.append(checker)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': c.name} for c in self.checkers]


def extract_checkers(code: str) -> List[Dict]:
    return CheckerExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
checker my_checker(input bit a, output bit b);
    bit temp;
endchecker
'''
    print(extract_checkers(test_code))
