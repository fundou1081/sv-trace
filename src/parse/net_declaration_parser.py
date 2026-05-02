"""
Net Declaration Parser - 使用正确的 AST 遍历

提取网络类型声明：
- wire, wand, wor, tri, triand, trior
- supply0, supply1
- uwire

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class NetDecl:
    name: str = ""
    net_type: str = ""  # wire, tri, etc.
    width: str = ""


class NetDeclarationExtractor:
    def __init__(self):
        self.nets: List[NetDecl] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'NetDeclaration':
                nd = NetDecl()
                
                if hasattr(node, 'keyword') and node.keyword:
                    nd.net_type = str(node.keyword).lower()
                
                if hasattr(node, 'name') and node.name:
                    nd.name = str(node.name)
                
                if nd.name:
                    self.nets.append(nd)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return [
            {'name': n.name, 'type': n.net_type}
            for n in self.nets
        ]


def extract_nets(code: str) -> List[Dict]:
    return NetDeclarationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
wire [7:0] data;
triand enable;
wor result;
'''
    result = extract_nets(test_code)
    print(f"Nets: {len(result)}")
