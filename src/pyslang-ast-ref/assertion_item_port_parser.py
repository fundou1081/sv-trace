"""
Assertion Item Port Parser - 使用正确的 AST 遍历

提取断言项端口：
- AssertionItemPort
- AssertionItemPortList

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class AssertionItemPort:
    name: str = ""
    data_type: str = ""


class AssertionItemPortExtractor:
    def __init__(self):
        self.ports: List[AssertionItemPort] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['AssertionItemPort', 'AssertionItemPortList']:
                aip = AssertionItemPort()
                if hasattr(node, 'name') and node.name:
                    aip.name = str(node.name)
                if hasattr(node, 'dataType') and node.dataType:
                    aip.data_type = str(node.dataType)[:25]
                self.ports.append(aip)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': p.name[:25], 'type': p.data_type[:20]} for p in self.ports]


def extract_assertion_ports(code: str) -> List[Dict]:
    return AssertionItemPortExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
property p(input a, input b);
endproperty
'''
    result = extract_assertion_ports(test_code)
    print(f"Assertion item ports: {len(result)}")
