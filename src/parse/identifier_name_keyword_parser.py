"""
Identifier Name Keyword Parser - 使用正确的 AST 遍历

提取标识符名称：
- IdentifierName

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class IdentifierName:
    name: str = ""


class IdentifierNameExtractor:
    def __init__(self):
        self.names: List[IdentifierName] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'IdentifierName':
                in_ = IdentifierName()
                in_.name = str(node)
                self.names.append(in_)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': n.name[:30]} for n in self.names[:100]]


def extract_identifier_names(code: str) -> List[Dict]:
    return IdentifierNameExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [7:0] my_signal;
'''
    result = extract_identifier_names(test_code)
    print(f"Identifier names: {len(result)}")
