"""
Variable Port Header Parser - 使用正确的 AST 遍历

提取变量端口头：
- VariablePortHeader
- AnsiPortDeclaration

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
class VariablePortHeader:
    name: str = ""
    direction: str = ""
    data_type: str = ""


class VariablePortHeaderExtractor:
    def __init__(self):
        self.headers: List[VariablePortHeader] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['VariablePortHeader', 'VariablePort']:
                vph = VariablePortHeader()
                if hasattr(node, 'name') and node.name:
                    vph.name = str(node.name)
                if hasattr(node, 'direction') and node.direction:
                    vph.direction = str(node.direction).lower()
                if hasattr(node, 'dataType') and node.dataType:
                    vph.data_type = str(node.dataType)[:30]
                self.headers.append(vph)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'name': h.name, 'direction': h.direction, 'type': h.data_type}
            for h in self.headers
        ]


def extract_variable_ports(code: str) -> List[Dict]:
    return VariablePortHeaderExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
function my_func(input [7:0] a, output [7:0] b);
endfunction
'''
    result = extract_variable_ports(test_code)
    for r in result:
        print(f"Port: {r['name']} ({r['direction']})")
