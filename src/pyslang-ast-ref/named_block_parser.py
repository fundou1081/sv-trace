"""
Named Block Parser - 使用正确的 AST 遍历

提取命名块：
- NamedBlockClause
- NamedBlock
- ElseClause
- EmptyStatement

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
class NamedBlock:
    name: str = ""


class NamedBlockExtractor:
    def __init__(self):
        self.blocks: List[NamedBlock] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['NamedBlockClause', 'NamedBlock']:
                nb = NamedBlock()
                if hasattr(node, 'name') and node.name:
                    nb.name = str(node.name)
                if nb.name:
                    self.blocks.append(nb)
            
            elif kind_name == 'ElseClause':
                nb = NamedBlock()
                nb.name = 'else'
                self.blocks.append(nb)
            
            elif kind_name == 'EmptyStatement':
                nb = NamedBlock()
                nb.name = 'empty'
                self.blocks.append(nb)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': b.name} for b in self.blocks]


def extract_named_blocks(code: str) -> List[Dict]:
    return NamedBlockExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
begin : block1
    // code
end : block1

if (a) begin
end else begin : else_block
end
'''
    result = extract_named_blocks(test_code)
    print(f"Named blocks: {len(result)}")
