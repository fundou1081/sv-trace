"""
Ordered Argument Parser - 使用正确的 AST 遍历

提取顺序参数：
- OrderedArgument
- NamedArgument

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
class ArgumentItem:
    name: str = ""
    value: str = ""
    is_ordered: bool = True


class OrderedArgumentExtractor:
    def __init__(self):
        self.arguments: List[ArgumentItem] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'OrderedArgument':
                a = ArgumentItem()
                a.is_ordered = True
                if hasattr(node, 'expression') and node.expression:
                    a.value = str(node.expression)[:50]
                elif hasattr(node, 'value') and node.value:
                    a.value = str(node.value)[:50]
                self.arguments.append(a)
            
            elif kind_name == 'NamedArgument':
                a = ArgumentItem()
                a.is_ordered = False
                if hasattr(node, 'name') and node.name:
                    a.name = str(node.name)
                if hasattr(node, 'value') and node.value:
                    a.value = str(node.value)[:50]
                elif hasattr(node, 'expression') and node.expression:
                    a.value = str(node.expression)[:50]
                self.arguments.append(a)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'name': a.name or '', 'value': a.value[:30], 'ordered': a.is_ordered}
            for a in self.arguments[:20]
        ]


def extract_arguments(code: str) -> List[Dict]:
    return OrderedArgumentExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
initial begin
    foo(a, b, c);
    bar(.x(1), .y(2));
end
'''
    result = extract_arguments(test_code)
    print(f"Arguments: {len(result)}")
