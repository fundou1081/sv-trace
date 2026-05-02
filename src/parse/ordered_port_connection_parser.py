"""
Ordered Port Connection Parser - 使用正确的 AST 遍历

提取顺序端口连接：
- OrderedPortConnection

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class OrderedPortConnection:
    position: int = 0
    value: str = ""


class OrderedPortConnectionExtractor:
    def __init__(self):
        self.connections: List[OrderedPortConnection] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['OrderedPortConnection', 'OrderedArgument']:
                opc = OrderedPortConnection()
                opc.position = len(self.connections)
                
                if hasattr(node, 'value') and node.value:
                    opc.value = str(node.value)[:30]
                elif hasattr(node, 'expression') and node.expression:
                    opc.value = str(node.expression)[:30]
                
                self.connections.append(opc)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'pos': c.position, 'value': c.value[:25]} for c in self.connections[:20]]


def extract_ordered_ports(code: str) -> List[Dict]:
    return OrderedPortConnectionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
mod u1 (a, b, c);
'''
    result = extract_ordered_ports(test_code)
    print(f"Ordered port connections: {len(result)}")
