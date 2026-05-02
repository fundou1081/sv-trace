"""
Cover Property Parser - 使用正确的 AST 遍历

提取 cover property 语句：
- CoverProperty

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
class CoverProperty:
    property_expr: str = ""
    action_block: str = ""


class CoverPropertyExtractor:
    def __init__(self):
        self.properties: List[CoverProperty] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'CoverProperty':
                cp = CoverProperty()
                if hasattr(node, 'property') and node.property:
                    cp.property_expr = str(node.property)
                if hasattr(node, 'action') and node.action:
                    cp.action_block = str(node.action)
                self.properties.append(cp)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'property': p.property_expr[:50], 'has_action': bool(p.action_block)}
            for p in self.properties
        ]


def extract_cover_properties(code: str) -> List[Dict]:
    return CoverPropertyExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
cover property (@(posedge clk) req |-> ack);
'''
    result = extract_cover_properties(test_code)
    print(f"Cover properties: {len(result)}")
