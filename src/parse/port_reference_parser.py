"""
Port Reference Parser - 使用正确的 AST 遍历

提取端口引用：
- PortReference

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class PortReference:
    port_name: str = ""


class PortReferenceExtractor:
    def __init__(self):
        self.references: List[PortReference] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'PortReference':
                pr = PortReference()
                if hasattr(node, 'port') and node.port:
                    pr.port_name = str(node.port)
                elif hasattr(node, 'name') and node.name:
                    pr.port_name = str(node.name)
                self.references.append(pr)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'port': r.port_name[:30]} for r in self.references]


def extract_port_references(code: str) -> List[Dict]:
    return PortReferenceExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
.port_ref(my_signal)
'''
    result = extract_port_references(test_code)
    print(f"Port references: {len(result)}")
