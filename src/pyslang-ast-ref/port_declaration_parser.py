"""
Port Declaration Parser - 使用正确的 AST 遍历

提取端口声明：
- PortDeclaration
- AnsiPortDeclaration
- NonAnsiPortDeclaration

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
class PortDecl:
    name: str = ""
    direction: str = ""  # input, output, inout, ref
    data_type: str = ""
    width: str = ""


class PortDeclarationExtractor:
    def __init__(self):
        self.ports: List[PortDecl] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['PortDeclaration', 'AnsiPortDeclaration', 'NonAnsiPortDeclaration']:
                pd = PortDecl()
                
                if hasattr(node, 'direction') and node.direction:
                    pd.direction = str(node.direction).lower()
                
                if hasattr(node, 'name') and node.name:
                    pd.name = str(node.name)
                
                if hasattr(node, 'dataType') and node.dataType:
                    pd.data_type = str(node.dataType)[:30]
                
                if pd.name:
                    self.ports.append(pd)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return [
            {'name': p.name, 'direction': p.direction, 'type': p.data_type[:20]}
            for p in self.ports
        ]


def extract_ports(code: str) -> List[Dict]:
    return PortDeclarationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test(
    input clk,
    input [7:0] data,
    output reg [7:0] q,
    ref logic enable
);
endmodule
'''
    result = extract_ports(test_code)
    for p in result:
        print(f"Port: {p['name']} ({p['direction']})")
