"""
ANSI Port List Parser - 使用正确的 AST 遍历

提取 ANSI 端口列表：
- AnsiPortList
- AnsiPortDeclaration
- ImplicitAnsiPort

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
class AnsiPort:
    name: str = ""
    direction: str = ""  # input, output, inout, ref
    data_type: str = ""
    width: str = ""


class AnsiPortListExtractor:
    def __init__(self):
        self.ports: List[AnsiPort] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['AnsiPortList', 'PortList']:
                for child in node:
                    if not child:
                        continue
                    port = self._extract_port(child)
                    if port:
                        self.ports.append(port)
            
            elif kind_name in ['AnsiPortDeclaration', 'ImplicitAnsiPort']:
                port = self._extract_port(node)
                if port:
                    self.ports.append(port)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_port(self, node):
        p = AnsiPort()
        
        if hasattr(node, 'name') and node.name:
            p.name = str(node.name)
        
        if hasattr(node, 'direction') and node.direction:
            p.direction = str(node.direction).lower()
        
        if hasattr(node, 'dataType') and node.dataType:
            p.data_type = str(node.dataType)[:30]
        
        if hasattr(node, 'width') and node.width:
            p.width = str(node.width)
        elif hasattr(node, 'dimensions') and node.dimensions:
            for dim in node.dimensions:
                p.width += str(dim) + ' '
        
        return p if p.name else None
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'name': p.name, 'direction': p.direction, 'type': p.data_type[:20]}
            for p in self.ports
        ]


def extract_ansi_ports(code: str) -> List[Dict]:
    return AnsiPortListExtractor().extract_from_text(code)


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
    result = extract_ansi_ports(test_code)
    for r in result:
        print(f"Port: {r['name']} ({r['direction']})")
