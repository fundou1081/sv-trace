"""
Null Literal Parser - 使用正确的 AST 遍历

提取 null 字面量：
- NullLiteralExpression

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
class NullLiteral:
    value: str = "null"


class NullLiteralExtractor:
    def __init__(self):
        self.literals: List[NullLiteral] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'NullLiteralExpression':
                nl = NullLiteral()
                if hasattr(node, 'value') and node.value:
                    nl.value = str(node.value)
                self.literals.append(nl)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'value': n.value} for n in self.literals]


def extract_null_literals(code: str) -> List[Dict]:
    return NullLiteralExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
class MyClass;
    MyClass obj = null;
endclass
'''
    result = extract_null_literals(test_code)
    print(f"Null literals: {len(result)}")
