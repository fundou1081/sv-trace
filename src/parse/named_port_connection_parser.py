"""
Named Port Connection Parser - 使用正确的 AST 遍历

提取命名端口连接：
- NamedPortConnection
- OrderedParamAssignment

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
class PortConnection:
    port_name: str = ""
    value: str = ""


class NamedPortConnectionExtractor:
    def __init__(self):
        self.connections: List[PortConnection] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['NamedPortConnection', 'NamedPort']:
                pc = PortConnection()
                if hasattr(node, 'name') and node.name:
                    pc.port_name = str(node.name)
                if hasattr(node, 'value') and node.value:
                    pc.value = str(node.value)[:30]
                elif hasattr(node, 'expression') and node.expression:
                    pc.value = str(node.expression)[:30]
                self.connections.append(pc)
            
            elif kind_name == 'OrderedParamAssignment':
                pc = PortConnection()
                pc.port_name = 'ordered_param'
                if hasattr(node, 'value') and node.value:
                    pc.value = str(node.value)[:30]
                self.connections.append(pc)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'port': c.port_name, 'value': c.value[:30]} for c in self.connections[:20]]


def extract_port_connections(code: str) -> List[Dict]:
    return NamedPortConnectionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
my_module u1 (.clk(clk), .data(data));
defines #(.WIDTH(8));
'''
    result = extract_port_connections(test_code)
    print(f"Port connections: {len(result)}")
