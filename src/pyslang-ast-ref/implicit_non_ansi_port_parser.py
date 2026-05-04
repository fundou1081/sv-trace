"""
Implicit Non-Ansi Port Parser - 使用正确的 AST 遍历

提取隐式非 ANSI 端口：
- ImplicitNonAnsiPort
- NonAnsiPortList

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ImplicitNonAnsiPort:
    name: str = ""
    direction: str = ""


class ImplicitNonAnsiPortExtractor:
    def __init__(self):
        self.ports: List[ImplicitNonAnsiPort] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ImplicitNonAnsiPort', 'NonAnsiPortList', 'NonAnsiPort']:
                inap = ImplicitNonAnsiPort()
                
                if hasattr(node, 'name') and node.name:
                    inap.name = str(node.name)
                
                if hasattr(node, 'direction') and node.direction:
                    inap.direction = str(node.direction).lower()
                
                self.ports.append(inap)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': p.name, 'direction': p.direction[:10]} for p in self.ports]


def extract_implicit_ports(code: str) -> List[Dict]:
    return ImplicitNonAnsiPortExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module m (a, b, c);
endmodule
'''
    result = extract_implicit_ports(test_code)
    print(f"Implicit non-ANSI ports: {len(result)}")
